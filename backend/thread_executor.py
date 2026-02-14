from typing import Callable, Any
import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)


async def run_in_thread(func: Callable, *args, **kwargs) -> Any:
    """
    Run a blocking function in a separate thread to avoid freezing the asyncio loop.

    Args:
        func: The blocking function to run
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call
    """
    loop = asyncio.get_running_loop()

    pfunc = functools.partial(func, *args, **kwargs)

    return await loop.run_in_executor(executor, pfunc)
