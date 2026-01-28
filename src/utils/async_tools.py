import functools
import threading
from typing import Callable, Any

def run_in_background(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to run a synchronous Flet event handler in a background thread.
    This prevents the UI from freezing during long-running Polars calculations.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # flet handlers typically receive a ControlEvent as the first argument (if not self)
        thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
        thread.start()
    return wrapper
