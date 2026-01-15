"""
Utility functions for reading large files efficiently using generators.
"""

from pathlib import Path
from typing import AsyncGenerator, Generator, Optional, Union

import aiofiles
from pypdf import PdfReader

from app.core.logging import logger


class FileStats:
    """Type definition for file statistics."""

    file_name: str
    file_size_bytes: int
    file_size_kb: float
    file_size_mb: float
    total_lines: Optional[int]
    total_chunks: Optional[int]
    total_characters: Optional[int]
    total_words: Optional[int]
    file_type: str
    chunk_size_used: int


async def read_large_file_async(
    file_path: Union[str, Path],
    chunk_size: int = 8192,
    encoding: str = "utf-8",
) -> AsyncGenerator[str, None]:
    """
    Asynchronously read a large file line by line using a generator.

    Args:
        file_path: Path to the file to read
        chunk_size: Size of chunks to read (default: 8192 bytes)
        encoding: File encoding (default: utf-8)

    Yields:
        str: Each line from the file

    Example:
        async for line in read_large_file_async("large_file.txt"):
            process(line)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"📖 Reading large file: {file_path}")
    line_count = 0

    try:
        async with aiofiles.open(file_path, mode="r", encoding=encoding) as file:
            async for line in file:
                line_count += 1
                yield line.rstrip("\n\r")

        logger.info(f"✅ Finished reading {line_count} lines from {file_path}")
    except Exception as e:
        logger.error(f"❌ Error reading file {file_path}: {e}")
        raise


def read_large_file_sync(
    file_path: Union[str, Path],
    chunk_size: int = 8192,
    encoding: str = "utf-8",
) -> Generator[str, None, None]:
    """
    Synchronously read a large file line by line using a generator.

    Args:
        file_path: Path to the file to read
        chunk_size: Size of chunks to read (default: 8192 bytes)
        encoding: File encoding (default: utf-8)

    Yields:
        str: Each line from the file

    Example:
        for line in read_large_file_sync("large_file.txt"):
            process(line)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"📖 Reading large file: {file_path}")
    line_count = 0

    try:
        with open(file_path, mode="r", encoding=encoding) as file:
            for line in file:
                line_count += 1
                yield line.rstrip("\n\r")

        logger.info(f"✅ Finished reading {line_count} lines from {file_path}")
    except Exception as e:
        logger.error(f"❌ Error reading file {file_path}: {e}")
        raise


async def read_file_in_chunks_async(
    file_path: Union[str, Path],
    chunk_size: int = 8192,
    encoding: str = "utf-8",
) -> AsyncGenerator[bytes, None]:
    """
    Asynchronously read a file in chunks (binary mode).

    Args:
        file_path: Path to the file to read
        chunk_size: Size of chunks to read in bytes
        encoding: File encoding (not used in binary mode)

    Yields:
        bytes: Chunk of file data
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"📖 Reading file in chunks: {file_path}")
    bytes_read = 0

    try:
        async with aiofiles.open(file_path, mode="rb") as file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_read += len(chunk)
                yield chunk

        logger.info(f"✅ Finished reading {bytes_read} bytes from {file_path}")
    except Exception as e:
        logger.error(f"❌ Error reading file {file_path}: {e}")
        raise


async def count_file_length_async(
    file_path: Union[str, Path],
    chunk_size: int = 8192,
) -> dict[str, str | int | float | None]:
    """
    Count file length (lines and bytes) using generator for memory efficiency.

    Args:
        file_path: Path to the file to analyze
        chunk_size: Size of chunks to read (default: 8192 bytes)

    Returns:
        dict[str, str | int | float | None]: File statistics including:
        - file_name: Name of the file
        - file_size_bytes: Total size in bytes
        - total_lines: Number of lines (for text files)
        - file_type: File extension

    Example:
        stats = await count_file_length_async("document.pdf")
        print(f"File has {stats['file_size_bytes']} bytes")
    """
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"📊 Analyzing file: {file_path}")

    # Get file size
    file_size = file_path.stat().st_size
    file_extension = file_path.suffix.lower()

    # Count lines for text files using generator
    line_count = 0
    if file_extension in [".txt", ".log", ".csv", ".json", ".xml"]:
        try:
            async for _ in read_large_file_async(file_path):
                line_count += 1
        except Exception as e:
            logger.warning(f"⚠️  Could not count lines for {file_path}: {e}")
            line_count = 0

    # For PDF files, extract text and count words
    chunk_count = 0
    total_characters = 0
    total_words = 0

    if file_extension == ".pdf":
        try:
            # Count chunks using generator
            async for chunk in read_file_in_chunks_async(file_path, chunk_size):
                chunk_count += 1

            # Extract text from PDF to count words
            try:
                pdf_reader = PdfReader(str(file_path))
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        total_words += len(text.split())
                        total_characters += len(text)
                logger.info(f"📄 Extracted text from {len(pdf_reader.pages)} pages")
            except Exception as e:
                logger.warning(f"⚠️  Could not extract text from PDF: {e}")
        except Exception as e:
            logger.warning(f"⚠️  Could not process PDF chunks: {e}")

    # For text files, count characters and words
    if file_extension in [".txt", ".log", ".csv", ".json", ".xml"]:
        try:
            async for line in read_large_file_async(file_path):
                total_characters += len(line)
                total_words += len(line.split())
        except Exception as e:
            logger.warning(f"⚠️  Could not count characters/words: {e}")

    stats = {
        "file_name": file_path.name,
        "file_size_bytes": file_size,
        "file_size_kb": round(file_size / 1024, 2),
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "total_lines": line_count if line_count > 0 else None,
        "total_chunks": chunk_count if chunk_count > 0 else None,
        "total_characters": total_characters if total_characters > 0 else None,
        "total_words": total_words if total_words > 0 else None,
        "file_type": file_extension,
        "chunk_size_used": chunk_size,
    }

    logger.info(f"✅ File analysis complete: {stats}")
    return stats
