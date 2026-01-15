"""
Custom decorators for the application.
"""
import time
import functools
import inspect
from typing import Callable, TypeVar, ParamSpec
from app.core.logging import logger

P = ParamSpec("P")
R = TypeVar("R")


def execution_timer(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to measure and log function execution time.
    
    Args:
        func: Function to be decorated
        
    Returns:
        Wrapped function with execution time logging
        
    Example:
        @execution_timer
        async def my_function():
            # function code
            pass
    """
    @functools.wraps(func)
    async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            logger.info(
                f"⏱️  Function '{func.__name__}' executed in {execution_time:.4f} seconds",
                function=func.__name__,
                execution_time=execution_time,
                module=func.__module__,
            )
            return result
        except Exception as e:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.error(
                f"❌ Function '{func.__name__}' failed after {execution_time:.4f} seconds",
                function=func.__name__,
                execution_time=execution_time,
                error=str(e),
                module=func.__module__,
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            
            logger.info(
                f"⏱️  Function '{func.__name__}' executed in {execution_time:.4f} seconds",
                function=func.__name__,
                execution_time=execution_time,
                module=func.__module__,
            )
            return result
        except Exception as e:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.error(
                f"❌ Function '{func.__name__}' failed after {execution_time:.4f} seconds",
                function=func.__name__,
                execution_time=execution_time,
                error=str(e),
                module=func.__module__,
            )
            raise
    
    # Return appropriate wrapper based on whether function is async
    if inspect.iscoroutinefunction(func):
        return async_wrapper  # type: ignore
    return sync_wrapper  # type: ignore
