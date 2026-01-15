"""
File upload schemas and response models.
"""

from typing import Optional

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """Response model for file upload."""

    success: bool
    message: str
    file_stats: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "File uploaded and analyzed successfully",
                "file_stats": {
                    "file_name": "document.pdf",
                    "file_size_bytes": 1048576,
                    "file_size_kb": 1024.0,
                    "file_size_mb": 1.0,
                    "total_chunks": 128,
                    "file_type": ".pdf",
                    "chunk_size_used": 8192,
                },
            }
        }


class FileAnalysisResponse(BaseModel):
    """Response model for file analysis."""

    file_name: str = Field(..., description="Name of the file")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_size_kb: float = Field(..., description="File size in KB")
    file_size_mb: float = Field(..., description="File size in MB")
    total_lines: Optional[int] = Field(
        None, description="Number of lines (for text files)"
    )
    total_chunks: Optional[int] = Field(None, description="Number of chunks processed")
    total_characters: Optional[int] = Field(None, description="Total character count")
    total_words: Optional[int] = Field(None, description="Total word count")
    file_type: str = Field(..., description="File extension")
    chunk_size_used: int = Field(..., description="Chunk size used for processing")

    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "document.pdf",
                "file_size_bytes": 1048576,
                "file_size_kb": 1024.0,
                "file_size_mb": 1.0,
                "total_lines": None,
                "total_chunks": 128,
                "file_type": ".pdf",
                "chunk_size_used": 8192,
            }
        }
