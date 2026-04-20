"""
Timeout handling for long-running analyses.
Provides both Unix signal-based and thread-based implementations.
"""
import signal
import threading
from functools import wraps
from typing import Callable, Any, Optional
import sys


class TimeoutException(Exception):
    """Raised when analysis exceeds timeout."""
    pass


class TimeoutHandler:
    """Handle analysis timeouts gracefully."""
    
    @staticmethod
    def timeout(seconds: int = 30):
        """
        Decorator to add timeout protection to functions.
        Uses signal on Unix, threading on Windows.
        
        Args:
            seconds: Timeout in seconds
            
        Usage:
            @timeout(30)
            def long_analysis(image):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Use signal on Unix systems
                if sys.platform != 'win32' and hasattr(signal, 'SIGALRM'):
                    def signal_handler(signum, frame):
                        raise TimeoutException(f"Analysis exceeded {seconds}s timeout")
                    
                    old_handler = signal.signal(signal.SIGALRM, signal_handler)
                    signal.alarm(seconds)
                    
                    try:
                        result = func(*args, **kwargs)
                        signal.alarm(0)  # Cancel alarm
                        return result
                    except TimeoutException:
                        raise
                    finally:
                        signal.signal(signal.SIGALRM, old_handler)
                
                # Use threading on Windows
                else:
                    result = [None]
                    exception = [None]
                    
                    def target():
                        try:
                            result[0] = func(*args, **kwargs)
                        except Exception as e:
                            exception[0] = e
                    
                    thread = threading.Thread(target=target, daemon=True)
                    thread.start()
                    thread.join(timeout=seconds)
                    
                    if thread.is_alive():
                        raise TimeoutException(f"Analysis exceeded {seconds}s timeout")
                    
                    if exception[0]:
                        raise exception[0]
                    
                    return result[0]
            
            return wrapper
        
        return decorator
    
    @staticmethod
    def with_graceful_fallback(timeout_seconds: int = 30, fallback_value: Any = None):
        """
        Decorator that catches timeout and returns fallback value instead of raising.
        
        Args:
            timeout_seconds: Timeout in seconds
            fallback_value: Value to return on timeout
            
        Usage:
            @with_graceful_fallback(30, fallback_value={'error': 'timeout'})
            def analyze(image):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return TimeoutHandler.timeout(timeout_seconds)(func)(*args, **kwargs)
                except TimeoutException as e:
                    # Return fallback with error info
                    if isinstance(fallback_value, dict):
                        return {
                            **fallback_value,
                            'error': str(e),
                            'timed_out': True
                        }
                    return fallback_value
            
            return wrapper
        
        return decorator
