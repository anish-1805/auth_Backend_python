"""
Global error handling middleware.
"""
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger


async def error_handler_middleware(request: Request, call_next) -> Response:
    """
    Global error handler for unhandled exceptions.
    
    Args:
        request: Incoming request
        call_next: Next middleware/handler
        
    Returns:
        Response: Response or error response
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(
            f"❌ Unhandled exception: {str(e)}",
            error=str(e),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "error": str(e) if settings.DEBUG else "An unexpected error occurred",
            },
        )
