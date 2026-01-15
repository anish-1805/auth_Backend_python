"""
File upload and processing routes.
"""
import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.features.files.schemas import FileUploadResponse, FileAnalysisResponse
from app.utils.file_reader import count_file_length_async
from app.features.auth.dependencies import get_current_user
from app.features.auth.schemas import UserResponse
from app.core.logging import logger
from app.core.config import settings

router = APIRouter(prefix="/files", tags=["files"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
) -> FileUploadResponse:
    """
    Upload a PDF file and analyze its length using generators.
    
    Args:
        file: Uploaded file (PDF only)
        current_user: Authenticated user
        
    Returns:
        FileUploadResponse with file statistics
        
    Raises:
        HTTPException: If file type is not allowed or file is too large
    """
    try:
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file_extension} not allowed. Only PDF files are supported."
            )
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size} bytes exceeds maximum allowed size of {MAX_FILE_SIZE} bytes"
            )
        
        # Create user-specific directory
        user_dir = UPLOAD_DIR / current_user.id
        user_dir.mkdir(exist_ok=True)
        
        # Save file with unique name
        file_path = user_dir / file.filename
        
        # If file exists, add counter
        counter = 1
        original_stem = file_path.stem
        while file_path.exists():
            file_path = user_dir / f"{original_stem}_{counter}{file_extension}"
            counter += 1
        
        logger.info(f"📤 Uploading file: {file.filename} for user: {current_user.email}")
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"✅ File saved: {file_path}")
        
        # Analyze file using generator
        file_stats = await count_file_length_async(file_path)
        
        return FileUploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded and analyzed successfully",
            file_stats=file_stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    finally:
        file.file.close()


@router.get("/analyze/{file_name}", response_model=FileAnalysisResponse)
async def analyze_uploaded_file(
    file_name: str,
    current_user: UserResponse = Depends(get_current_user),
) -> FileAnalysisResponse:
    """
    Analyze a previously uploaded file using generators.
    
    Args:
        file_name: Name of the file to analyze
        current_user: Authenticated user
        
    Returns:
        FileAnalysisResponse with file statistics
        
    Raises:
        HTTPException: If file not found
    """
    try:
        # Get user's file directory
        user_dir = UPLOAD_DIR / current_user.id
        file_path = user_dir / file_name
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_name}' not found"
            )
        
        logger.info(f"📊 Analyzing file: {file_name} for user: {current_user.email}")
        
        # Analyze file using generator
        file_stats = await count_file_length_async(file_path)
        
        return FileAnalysisResponse(**file_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze file: {str(e)}"
        )


@router.delete("/delete/{file_name}")
async def delete_uploaded_file(
    file_name: str,
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """
    Delete a previously uploaded file.
    
    Args:
        file_name: Name of the file to delete
        current_user: Authenticated user
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If file not found
    """
    try:
        # Get user's file directory
        user_dir = UPLOAD_DIR / current_user.id
        file_path = user_dir / file_name
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_name}' not found"
            )
        
        logger.info(f"🗑️  Deleting file: {file_name} for user: {current_user.email}")
        
        # Delete file
        file_path.unlink()
        
        return {
            "success": True,
            "message": f"File '{file_name}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/list")
async def list_uploaded_files(
    current_user: UserResponse = Depends(get_current_user),
) -> dict:
    """
    List all uploaded files for the current user.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of uploaded files with their stats
    """
    try:
        # Get user's file directory
        user_dir = UPLOAD_DIR / current_user.id
        
        if not user_dir.exists():
            return {
                "success": True,
                "files": [],
                "total_files": 0
            }
        
        logger.info(f"📋 Listing files for user: {current_user.email}")
        
        # Get all files
        files = []
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                file_stats = await count_file_length_async(file_path)
                files.append(file_stats)
        
        return {
            "success": True,
            "files": files,
            "total_files": len(files)
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list files: {str(e)}"
        )
