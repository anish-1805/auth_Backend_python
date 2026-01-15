"""
Authentication routes and endpoints.
"""

from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Cookie,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.features.auth.dependencies import get_auth_repository, get_current_user
from app.features.auth.repository import AuthRepository
from app.features.auth.schemas import (
    AuthResponse,
    ChangePasswordRequest,
    DeleteUsersRequest,
    EmailOnlyRequest,
    LoginRequest,
    OTPVerificationRequest,
    PaginatedUsersResponse,
    PaginationParams,
    ResetPasswordRequest,
    SignupRequest,
    UpdateProfileRequest,
    UserResponse,
)
from app.middleware.rate_limit import rate_limit_middleware
from app.services.background_tasks import (
    send_password_reset_otp_background,
    send_password_reset_success_background,
    send_signup_otp_background,
)
from app.utils.decorators import execution_timer
from app.utils.jwt import create_access_token
from app.utils.otp import generate_otp_with_expiry, verify_otp
from app.utils.password import hash_password, verify_password

router = APIRouter()


def set_jwt_cookie(response: Response, token: str) -> None:
    """
    Set JWT token as httpOnly cookie.

    Args:
        response: FastAPI response object
        token: JWT token
    """
    max_age = settings.COOKIE_EXPIRES_IN * 24 * 60 * 60  # Convert days to seconds

    response.set_cookie(
        key="jwt",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=max_age,
        path="/",
    )


def clear_jwt_cookie(response: Response) -> None:
    """
    Clear JWT cookie.

    Args:
        response: FastAPI response object
    """
    response.delete_cookie(
        key="jwt",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )


@router.post(
    "/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED
)
@execution_timer
async def signup(
    body: SignupRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    User signup endpoint - Step 1: Create user and send OTP.
    """
    await rate_limit_middleware(http_request)

    # Check if user already exists
    existing_user = await repository.find_by_email(body.email)

    if existing_user:
        # Handle social login user trying to set password
        if existing_user.isSocialLogin and not existing_user.password:
            hashed_password = hash_password(body.password)

            await repository.update_user(
                existing_user.id,
                {
                    "password": hashed_password,
                    "provider": "local",
                    "name": body.name.strip(),
                },
            )

            # Generate and store OTP
            otp_data = generate_otp_with_expiry(settings.OTP_EXPIRY_MINUTES)
            await repository.update_user_otp(existing_user.id, "signupOTP", otp_data)

            # Send OTP email in background
            background_tasks.add_task(
                send_signup_otp_background,
                existing_user.email,
                body.name.strip(),
                str(otp_data["otp"]),
            )

            return AuthResponse(
                success=True,
                message="Password set successfully for your Google account. Please verify your email with the OTP sent.",
                data={
                    "email": existing_user.email,
                    "otpSent": True,
                    "expiresIn": "5 minutes",
                    "accountLinked": True,
                },
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "User with this email already exists",
            },
        )

    # Hash password
    hashed_password = hash_password(body.password)

    # Create user
    user = await repository.create_user(
        name=body.name.strip(),
        email=body.email,
        password=hashed_password,
    )

    # Generate and store OTP
    otp_data = generate_otp_with_expiry(settings.OTP_EXPIRY_MINUTES)
    await repository.update_user_otp(user.id, "signupOTP", otp_data)

    # Send OTP email in background
    background_tasks.add_task(
        send_signup_otp_background,
        user.email,
        body.name.strip(),
        str(otp_data["otp"]),
    )

    return AuthResponse(
        success=True,
        message="Account created successfully. Please check your email for the verification code.",
        data={
            "email": user.email,
            "otpSent": True,
            "expiresIn": "5 minutes",
        },
    )


@router.post("/verify-signup-otp", response_model=AuthResponse)
@execution_timer
async def verify_signup_otp(
    body: OTPVerificationRequest,
    http_request: Request,
    response: Response,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Verify signup OTP and complete registration.
    """
    await rate_limit_middleware(http_request)

    # Find user with OTP data
    user = await repository.find_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found"},
        )

    # Check if already verified
    if user.isEmailVerified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Email is already verified"},
        )

    # Check if OTP exists
    if not user.signupOTP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "No OTP found. Please request a new one.",
            },
        )

    # Verify OTP
    otp_verification = verify_otp(
        body.otp,
        str(user.signupOTP["otp"]),
        str(user.signupOTP["expiryTime"]),
        bool(user.signupOTP["isUsed"]),
    )

    if not otp_verification["isValid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": otp_verification["error"]},
        )

    # Mark as verified
    verified_user = await repository.verify_signup_otp(body.email, body.otp)
    if not verified_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to verify user"},
        )

    # Generate JWT token for automatic login
    token = create_access_token(
        {"userId": verified_user.id, "email": verified_user.email}
    )

    # Set JWT cookie
    set_jwt_cookie(response, token)

    return AuthResponse(
        success=True,
        message="Email verified successfully! You are now logged in.",
        user=UserResponse.model_validate(verified_user),
    )


@router.post("/resend-signup-otp", response_model=AuthResponse)
@execution_timer
async def resend_signup_otp(
    body: EmailOnlyRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Resend signup OTP.
    """
    await rate_limit_middleware(http_request)

    user = await repository.find_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found"},
        )

    if user.isEmailVerified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Email is already verified"},
        )

    # Generate new OTP
    otp_data = generate_otp_with_expiry(settings.OTP_EXPIRY_MINUTES)
    await repository.update_user_otp(user.id, "signupOTP", otp_data)

    # Send OTP email in background
    background_tasks.add_task(
        send_signup_otp_background,
        user.email,
        user.name,
        str(otp_data["otp"]),
    )

    return AuthResponse(
        success=True,
        message="Verification code resent successfully. Please check your email.",
        data={"email": user.email, "otpSent": True, "expiresIn": "5 minutes"},
    )


@router.post("/login", response_model=AuthResponse)
@execution_timer
async def login(
    body: LoginRequest,
    http_request: Request,
    response: Response,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    User login endpoint.
    """
    await rate_limit_middleware(http_request)

    # Find user by email
    user = await repository.find_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "Invalid email or password"},
        )

    # Check if social login user without password
    if user.isSocialLogin and not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "This account was created using Google login. Please sign in with Google or set a password by signing up again.",
                "isSocialLogin": True,
                "provider": user.provider,
            },
        )

    # Check if email is verified
    if not user.isEmailVerified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Please verify your email before logging in. Check your inbox for the verification code.",
                "requiresEmailVerification": True,
                "email": user.email,
            },
        )

    # Verify password
    if not user.password or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "Invalid email or password"},
        )

    # Generate JWT token
    token = create_access_token({"userId": user.id, "email": user.email})

    # Set JWT cookie
    set_jwt_cookie(response, token)

    return AuthResponse(
        success=True,
        message="Login successful",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", response_model=AuthResponse)
@execution_timer
async def logout(
    http_request: Request,
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
) -> AuthResponse:
    """
    User logout endpoint.
    """
    await rate_limit_middleware(http_request)

    # Clear JWT cookie
    clear_jwt_cookie(response)

    return AuthResponse(success=True, message="Logout successful")


@router.get("/me", response_model=AuthResponse)
@execution_timer
async def get_current_user_info(
    http_request: Request,
    current_user: UserResponse = Depends(get_current_user),
) -> AuthResponse:
    """
    Get current user information.
    """
    await rate_limit_middleware(http_request)

    return AuthResponse(
        success=True, message="User retrieved successfully", user=current_user
    )


@router.post("/refresh", response_model=AuthResponse)
@execution_timer
async def refresh_token(
    http_request: Request,
    response: Response,
    jwt: Optional[str] = Cookie(None),
    current_user: UserResponse = Depends(get_current_user),
) -> AuthResponse:
    """
    Refresh JWT token.
    """
    await rate_limit_middleware(http_request)

    if not jwt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "No token provided"},
        )

    # Generate new token
    new_token = create_access_token(
        {"userId": current_user.id, "email": current_user.email}
    )

    # Set new JWT cookie
    set_jwt_cookie(response, new_token)

    return AuthResponse(success=True, message="Token refreshed successfully")


@router.put("/change-password", response_model=AuthResponse)
@execution_timer
async def change_password(
    body: ChangePasswordRequest,
    http_request: Request,
    current_user: UserResponse = Depends(get_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Change user password.
    """
    await rate_limit_middleware(http_request)

    # Get user with password
    user = await repository.find_by_id(current_user.id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found"},
        )

    # Verify current password
    if not user.password or not verify_password(body.currentPassword, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "Current password is incorrect"},
        )

    # Check if new password is different
    if user.password and verify_password(body.newPassword, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "New password must be different from current password",
            },
        )

    # Hash and update password
    hashed_password = hash_password(body.newPassword)
    await repository.update_user(current_user.id, {"password": hashed_password})

    return AuthResponse(success=True, message="Password changed successfully")


@router.put("/profile", response_model=AuthResponse)
@execution_timer
async def update_profile(
    body: UpdateProfileRequest,
    http_request: Request,
    current_user: UserResponse = Depends(get_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Update user profile.
    """
    await rate_limit_middleware(http_request)

    # Check if email is being changed and if it's already taken
    if body.email and body.email != current_user.email:
        existing_user = await repository.find_by_email(body.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Email is already taken by another user",
                },
            )

    # Prepare update data
    update_data = {}
    if body.name:
        update_data["name"] = body.name.strip()
    if body.email:
        update_data["email"] = body.email.lower().strip()

    # Update user
    updated_user = await repository.update_user(current_user.id, update_data)

    return AuthResponse(
        success=True,
        message="Profile updated successfully",
        user=UserResponse.model_validate(updated_user),
    )


@router.post("/forgot-password", response_model=AuthResponse)
@execution_timer
async def forgot_password(
    body: EmailOnlyRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Initiate password reset process.
    """
    await rate_limit_middleware(http_request)

    user = await repository.find_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found with this email"},
        )

    # Generate OTP
    otp_data = generate_otp_with_expiry(settings.OTP_EXPIRY_MINUTES)
    await repository.update_user_otp(user.id, "passwordResetOTP", otp_data)

    # Send OTP email in background
    background_tasks.add_task(
        send_password_reset_otp_background,
        user.email,
        user.name,
        str(otp_data["otp"]),
    )

    return AuthResponse(
        success=True,
        message="Password reset code sent to your email. Please check your inbox.",
        data={"email": user.email, "otpSent": True, "expiresIn": "5 minutes"},
    )


@router.post("/verify-password-reset-otp", response_model=AuthResponse)
@execution_timer
async def verify_password_reset_otp(
    body: OTPVerificationRequest,
    http_request: Request,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Verify password reset OTP.
    """
    await rate_limit_middleware(http_request)

    user = await repository.find_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found"},
        )

    if not user.passwordResetOTP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "No OTP found. Please request a new one.",
            },
        )

    # Verify OTP
    otp_verification = verify_otp(
        body.otp,
        str(user.passwordResetOTP["otp"]),
        str(user.passwordResetOTP["expiryTime"]),
        bool(user.passwordResetOTP["isUsed"]),
    )

    if not otp_verification["isValid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": otp_verification["error"]},
        )

    return AuthResponse(
        success=True,
        message="OTP verified successfully. You can now reset your password.",
        data={"email": body.email, "otpVerified": True},
    )


@router.post("/reset-password", response_model=AuthResponse)
@execution_timer
async def reset_password(
    body: ResetPasswordRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Reset password with verified OTP.
    """
    await rate_limit_middleware(http_request)

    user = await repository.find_by_email(body.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "User not found"},
        )

    if not user.passwordResetOTP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "No OTP found. Please request a new one.",
            },
        )

    # Verify OTP
    otp_verification = verify_otp(
        body.otp,
        str(user.passwordResetOTP["otp"]),
        str(user.passwordResetOTP["expiryTime"]),
        bool(user.passwordResetOTP["isUsed"]),
    )

    if not otp_verification["isValid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": otp_verification["error"]},
        )

    # Hash and update password
    hashed_password = hash_password(body.newPassword)
    await repository.update_user(user.id, {"password": hashed_password})

    # Mark OTP as used
    await repository.update_user_otp(user.id, "passwordResetOTP", {"isUsed": True})

    # Send success email in background
    background_tasks.add_task(
        send_password_reset_success_background,
        user.email,
        user.name,
    )

    return AuthResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password.",
    )


@router.get("/users", response_model=PaginatedUsersResponse)
@execution_timer
async def get_all_users(
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    sortBy: str = "createdAt",
    sortOrder: str = "desc",
    current_user: UserResponse = Depends(get_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> PaginatedUsersResponse:
    """
    Get all users with pagination and search (CRUD operation).
    """
    users, total = await repository.get_all_users(
        page, limit, search, sortBy, sortOrder
    )

    total_pages = (total + limit - 1) // limit
    has_more = page < total_pages

    return PaginatedUsersResponse(
        success=True,
        users=[UserResponse.model_validate(user) for user in users],
        pagination={
            "currentPage": page,
            "totalPages": total_pages,
            "totalItems": total,
            "itemsPerPage": limit,
            "hasMore": has_more,
        },
    )


@router.delete("/users/delete", response_model=AuthResponse)
@execution_timer
async def delete_users(
    request: DeleteUsersRequest,
    current_user: UserResponse = Depends(get_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthResponse:
    """
    Delete multiple users in bulk (CRUD operation).
    """
    deleted_count, failed_deletions = await repository.delete_users_bulk(
        request.userIds, current_user.id
    )

    message = f"Successfully deleted {deleted_count} user(s)"
    if failed_deletions:
        message += f", {len(failed_deletions)} deletion(s) failed"

    return AuthResponse(
        success=True,
        message=message,
        data={
            "deletedCount": deleted_count,
            "failedDeletions": failed_deletions if failed_deletions else [],
        },
    )


@router.get("/socket-token", response_model=AuthResponse)
@execution_timer
async def get_socket_token(
    jwt: Optional[str] = Cookie(None),
    current_user: UserResponse = Depends(get_current_user),
) -> AuthResponse:
    """
    Get JWT token for Socket.IO authentication.
    """
    if jwt:
        return AuthResponse(success=True, message="Token retrieved", data={"token": jwt})
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "message": "No token available"},
        )


@router.get("/google")
@execution_timer
async def google_login() -> RedirectResponse:
    """
    Initiate Google OAuth login flow.
    Redirects user to Google's OAuth consent screen.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Google OAuth is not configured"},
        )

    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline&"
        f"prompt=consent"
    )

    logger.info("🔐 Redirecting to Google OAuth")
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
@execution_timer
async def google_callback(
    code: str,
    response: Response,
    repository: AuthRepository = Depends(get_auth_repository),
):
    """
    Handle Google OAuth callback with authorization code.

    Args:
        code: Authorization code from Google
        response: FastAPI response object
        repository: Auth repository

    Returns:
        RedirectResponse to frontend with success/error
    """
    try:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"success": False, "message": "Google OAuth is not configured"},
            )

        # Exchange authorization code for access token
        import httpx

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            tokens = token_response.json()

        # Get user info using access token
        access_token = tokens.get("access_token")
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"

        async with httpx.AsyncClient() as client:
            userinfo_response = await client.get(
                userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            userinfo_response.raise_for_status()
            user_info = userinfo_response.json()

        # Extract user information
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name", "")
        email_verified = user_info.get("verified_email", False)

        if not email or not google_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Invalid Google response"},
            )

        logger.info(f"🔐 Google OAuth callback for: {email}")

        # Check if user exists
        user = await repository.find_by_email(email)

        if user:
            # User exists - check if it's a Google account
            if not user.isSocialLogin or user.providerId != google_id:
                # Update to Google login
                await repository.update_user(
                    user.id,
                    {
                        "isSocialLogin": True,
                        "providerId": google_id,
                        "isEmailVerified": True,
                    },
                )
                user = await repository.find_by_id(user.id)

            logger.info(f"✅ Existing Google user logged in: {email}")
        else:
            # Create new user with Google account
            user = await repository.create_user(
                name=name or email.split("@")[0],
                email=email,
                password=None,
                provider="google",
                provider_id=google_id,
                is_social_login=True,
            )
            logger.info(f"✅ New Google user created: {email}")

        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"success": False, "message": "Failed to create/retrieve user"},
            )

        # Generate JWT token
        token = create_access_token({"userId": user.id, "email": user.email})

        # Return HTML page that sets cookie via JavaScript and redirects
        # This is necessary because cookies set during cross-origin redirects don't persist
        max_age = settings.COOKIE_EXPIRES_IN * 24 * 60 * 60
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Completing Google Sign In...</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                }}
                .spinner {{
                    border: 3px solid #f3f3f3;
                    border-top: 3px solid #667eea;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                h2 {{ color: #333; margin-bottom: 10px; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>✓ Google Sign In Successful</h2>
                <div class="spinner"></div>
                <p>Redirecting to dashboard...</p>
            </div>
            <script>
                // Set cookie with JWT token
                document.cookie = "jwt={token}; path=/; max-age={max_age}; SameSite=Lax";
                
                // Redirect to dashboard after cookie is set
                setTimeout(function() {{
                    window.location.href = "{settings.FRONTEND_URL}/dashboard";
                }}, 500);
            </script>
        </body>
        </html>
        """

        logger.info(
            f"✅ Google login successful for {email}, returning HTML with cookie"
        )
        return HTMLResponse(content=html_content, status_code=200)

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ Google API error: {e}")
        error_url = f"{settings.FRONTEND_URL}/login?error=google_auth_failed"
        return RedirectResponse(url=error_url)
    except Exception as e:
        logger.error(f"❌ Google OAuth error: {e}")
        error_url = f"{settings.FRONTEND_URL}/login?error=auth_failed"
        return RedirectResponse(url=error_url)


@router.get("/health", response_model=AuthResponse)
async def health_check() -> AuthResponse:
    """
    Auth service health check.
    """
    return AuthResponse(success=True, message="Auth service is running")
