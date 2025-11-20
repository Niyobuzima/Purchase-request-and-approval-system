"""
Custom cache backend for Upstash Redis.
"""
import pickle
import base64
from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT
from upstash_redis import Redis


class UpstashRedisCache(BaseCache):
    """
    Django cache backend using Upstash Redis.

    Configuration in settings:
        CACHES = {
            'default': {
                'BACKEND': 'core.cache.UpstashRedisCache',
                'OPTIONS': {
                    'UPSTASH_REDIS_REST_URL': 'your-url',
                    'UPSTASH_REDIS_REST_TOKEN': 'your-token',
                }
            }
        }

    Or use environment variables:
        UPSTASH_REDIS_REST_URL
        UPSTASH_REDIS_REST_TOKEN
    """

    def __init__(self, server, params):
        super().__init__(params)
        options = params.get('OPTIONS', {})

        # Try to get credentials from OPTIONS first, then from environment
        url = options.get('UPSTASH_REDIS_REST_URL')
        token = options.get('UPSTASH_REDIS_REST_TOKEN')

        if url and token:
            # Use explicit credentials from OPTIONS
            self._client = Redis(url=url, token=token)
        else:
            # Try to read from environment variables
            import os
            url = os.environ.get('UPSTASH_REDIS_REST_URL')
            token = os.environ.get('UPSTASH_REDIS_REST_TOKEN')

            if url and token:
                self._client = Redis(url=url, token=token)
            else:
                raise ValueError(
                    "Upstash Redis credentials not found. "
                    "Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN environment variables, "
                    "or provide them in CACHES['OPTIONS']"
                )

    def _make_key(self, key, version=None):
        """Construct the key with version and prefix."""
        if version is None:
            version = self.version

        new_key = f"{self.key_prefix}:{version}:{key}"
        return new_key

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a value in the cache if the key does not already exist.
        Returns True if the value was stored, False otherwise.
        """
        key = self._make_key(key, version=version)
        timeout = self.get_backend_timeout(timeout)

        pickled = pickle.dumps(value)
        encoded = base64.b64encode(pickled).decode('ascii')

        if timeout is None:
            # Set without expiration
            result = self._client.setnx(key, encoded)
        else:
            # Use SET with NX (only set if not exists) and EX (expiration)
            result = self._client.set(key, encoded, nx=True, ex=int(timeout))

        return bool(result)

    def get(self, key, default=None, version=None):
        """Fetch a value from the cache."""
        key = self._make_key(key, version=version)

        value = self._client.get(key)

        if value is None:
            return default

        try:
            # Decode from base64 then unpickle
            decoded = base64.b64decode(value)
            return pickle.loads(decoded)
        except (pickle.PickleError, ValueError):
            return default

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        """Set a value in the cache."""
        key = self._make_key(key, version=version)
        timeout = self.get_backend_timeout(timeout)

        pickled = pickle.dumps(value)
        encoded = base64.b64encode(pickled).decode('ascii')

        if timeout is None:
            self._client.set(key, encoded)
        else:
            self._client.setex(key, int(timeout), encoded)

    def delete(self, key, version=None):
        """Delete a key from the cache."""
        key = self._make_key(key, version=version)
        return bool(self._client.delete(key))

    def has_key(self, key, version=None):
        """Check if a key exists in the cache."""
        key = self._make_key(key, version=version)
        return bool(self._client.exists(key))

    def clear(self):
        """Clear all keys with the current prefix from the cache.

        Uses SCAN instead of KEYS to avoid blocking Redis in production.
        SCAN iterates through keys in chunks, preventing server freeze.
        """
        pattern = f"{self.key_prefix}:*"
        cursor = 0
        batch_size = 100  # Process keys in batches

        # Use SCAN to iterate through keys without blocking Redis
        while True:
            # SCAN returns (cursor, [keys])
            cursor, keys = self._client.scan(cursor, match=pattern, count=batch_size)

            # Delete keys in current batch
            if keys:
                self._client.delete(*keys)

            # cursor = 0 means we've completed the full scan
            if cursor == 0:
                break

    def get_many(self, keys, version=None):
        """Fetch multiple values at once."""
        key_map = {k: self._make_key(k, version=version) for k in keys}

        if not key_map:
            return {}

        values = self._client.mget(list(key_map.values()))

        result = {}
        for original_key, cache_key in key_map.items():
            idx = list(key_map.values()).index(cache_key)
            value = values[idx] if idx < len(values) else None

            if value is not None:
                try:
                    decoded = base64.b64decode(value)
                    result[original_key] = pickle.loads(decoded)
                except (pickle.PickleError, ValueError):
                    pass

        return result

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        """Set multiple values at once."""
        timeout = self.get_backend_timeout(timeout)

        pipeline = []
        for key, value in data.items():
            cache_key = self._make_key(key, version=version)
            pickled = pickle.dumps(value)
            encoded = base64.b64encode(pickled).decode('ascii')

            if timeout is None:
                self._client.set(cache_key, encoded)
            else:
                self._client.setex(cache_key, int(timeout), encoded)

    def delete_many(self, keys, version=None):
        """Delete multiple keys at once."""
        cache_keys = [self._make_key(k, version=version) for k in keys]
        if cache_keys:
            self._client.delete(*cache_keys)

    def incr(self, key, delta=1, version=None):
        """Increment a value in the cache."""
        key = self._make_key(key, version=version)

        try:
            value = self._client.incr(key, delta)
            return value
        except Exception:
            raise ValueError(f"Key '{key}' not found or not an integer")

    def decr(self, key, delta=1, version=None):
        """Decrement a value in the cache."""
        key = self._make_key(key, version=version)

        try:
            value = self._client.decr(key, delta)
            return value
        except Exception:
            raise ValueError(f"Key '{key}' not found or not an integer")

    def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        """Update the expiration time of a key."""
        key = self._make_key(key, version=version)
        timeout = self.get_backend_timeout(timeout)

        if timeout is None:
            # Remove expiration
            return bool(self._client.persist(key))
        else:
            # Set new expiration
            return bool(self._client.expire(key, int(timeout)))
