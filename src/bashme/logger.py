import logging
from typing import Any, Callable

from decorator import decorator


logger = logging.getLogger(__name__)


@decorator
def log_io(f: Callable, *args: Any, **kwargs: Any) -> Any:
    """A decorator that logs the inputs and outputs of a function."""
    args_str = ", ".join(map(repr, args))
    kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
    logger.debug(
        f"--> calling {f.__name__=} with args: {args_str} and kwargs: {{{kwargs_str}}}"
    )
    try:
        output = f(*args, **kwargs)
        logger.debug(f"<-- {output=}")
        return output
    except Exception as e:
        logger.exception(f"[!] {f.__name__=} raised an exception {e}")
        raise
