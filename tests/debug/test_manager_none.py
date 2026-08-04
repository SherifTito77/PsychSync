import asyncio

from app.core.cache import cache_get

# If cache_manager is None, cache_get returns None.
# If it returns None, 'or []' should turn it into [].
# The error says 'coroutine' object has no attribute 'get',
# which means cache_get returned a COROUTINE, not None, not a value.
# But cache_get IS a coroutine function, so if I don't await it,
# it returns a coroutine object.
# Wait, did I forget to await cache_get in account_security.py?
# I see 'attempts = await cache_get(cache_key) or []'.
# This should await cache_get.
# Is it possible that get_cache_manager() is returning a COROUTINE?
# No, it's a function.
