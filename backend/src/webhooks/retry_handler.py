"""
AMDI-OS Webhook & Event System: Retry Handler
=============================================

Implements exponential backoff and jitter calculations for webhook delivery, 
ensuring robust handling of temporary receiver downtime.
"""

import asyncio
import random
from typing import Callable, Any, Awaitable


def calculate_backoff(
    attempt: int, 
    base: float = 1.0, 
    factor: float = 2.0, 
    max_delay: float = 30.0, 
    jitter: bool = True
) -> float:
    """
    Computes exponential backoff: delay = base * (factor^attempt)
    If jitter is True, applies random fractional delay: delay + random(0, 0.5 * delay)
    """
    if attempt < 0:
        raise ValueError("Attempt number cannot be negative.")
        
    delay = base * (factor ** attempt)
    
    if jitter:
        # Add random jitter up to 50% of the computed delay
        delay += random.uniform(0.0, 0.5 * delay)
        
    return min(delay, max_delay)


async def execute_with_retry(
    func: Callable[[], Awaitable[Any]],
    max_attempts: int = 5,
    base: float = 1.0,
    factor: float = 2.0,
    max_delay: float = 30.0,
    on_retry: Callable[[int, Exception, float], None] = None
) -> Any:
    """
    Executes an async function, retrying with exponential backoff on failures.
    """
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise e
                
            delay = calculate_backoff(attempt, base, factor, max_delay, jitter=True)
            if on_retry:
                on_retry(attempt + 1, e, delay)
            await asyncio.sleep(delay)
