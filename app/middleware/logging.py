"""
Request logging middleware.
"""

import time

from fastapi import Request, Response

from app.core.logging import logger


async def logging_middleware(request: Request, call_next) -> Response:
    """
    Log all incoming requests and their processing time.

    Args:
        request: Incoming request
        call_next: Next middleware/handler

    Returns:
        Response: Response from handler
    """
    start_time = time.perf_counter()

    # Log request
    logger.info(
        f"📥 {request.method} {request.url.path}",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown",
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.perf_counter() - start_time

    # Log response
    logger.info(
        f"📤 {request.method} {request.url.path} - {response.status_code} ({process_time:.4f}s)",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time,
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response
