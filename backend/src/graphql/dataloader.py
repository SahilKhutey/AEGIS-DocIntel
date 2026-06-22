"""
AMDI-OS GraphQL API: DataLoader
================================

Implements the DataLoader batch loading pattern to resolve relationships in 
batches, preventing N+1 database/service query issues in async contexts.
"""

from typing import Callable, List, Dict, Any, Awaitable, Optional
import asyncio


class DataLoader:
    """
    Batches and caches loading of resources.
    Keys are collected during a single tick of the event loop and then resolved
    in a single batch call.
    """
    def __init__(self, batch_load_fn: Callable[[List[Any]], Awaitable[List[Any]]]):
        self._batch_load_fn = batch_load_fn
        self._queue: List[Any] = []
        self._futures: Dict[Any, List[asyncio.Future]] = {}
        self._cache: Dict[Any, Any] = {}

    async def load(self, key: Any) -> Any:
        """
        Loads a key, returning a promise/future for the value.
        If the key is already in the cache, returns the cached value.
        """
        if key in self._cache:
            return self._cache[key]

        if key not in self._futures:
            self._futures[key] = []
            self._queue.append(key)

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._futures[key].append(future)

        # Trigger batch dispatch on the next event loop iteration
        if len(self._queue) == 1:
            loop.call_soon(self._schedule_dispatch)

        return await future

    def _schedule_dispatch(self) -> None:
        asyncio.create_task(self.dispatch())

    async def dispatch(self) -> None:
        """
        Resolves all queued keys in a single batch.
        """
        if not self._queue:
            return

        current_keys = list(self._queue)
        self._queue.clear()

        try:
            results = await self._batch_load_fn(current_keys)
            
            # Map results to keys
            for key, val in zip(current_keys, results):
                self._cache[key] = val
                futs = self._futures.pop(key, [])
                for fut in futs:
                    if not fut.done():
                        fut.set_result(val)
        except Exception as e:
            # Handle exception by setting failure on all futures in this batch
            for key in current_keys:
                futs = self._futures.pop(key, [])
                for fut in futs:
                    if not fut.done():
                        fut.set_exception(e)

    def clear(self, key: Any) -> None:
        """
        Clears a specific key from the cache.
        """
        if key in self._cache:
            del self._cache[key]

    def clear_all(self) -> None:
        """
        Clears the entire cache.
        """
        self._cache.clear()

    def prime(self, key: Any, val: Any) -> None:
        """
        Primes the cache with a key and value.
        """
        if key not in self._cache:
            self._cache[key] = val
