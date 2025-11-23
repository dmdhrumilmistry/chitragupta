"""
Mixins for Chitragupta API.
"""

from json import dumps
from hashlib import sha256
from django.core.cache import cache
from rest_framework.response import Response


class FilteredCacheMixin:
    """
    Cache list responses keyed by allowed filterset fields + page + a version token.
    - set `cache_timeout` (seconds)
    - set `cache_filters` (iterable of query param names) or rely on view.filterset_fields
    - set `cache_version_key` to the cache key used as version token (e.g. "repo_version")
    """
    cache_timeout = 60 * 15
    cache_filters = None
    cache_version_key = None  # e.g. "repo_version"

    def get_cache_filters(self):
        """
        Return the list of allowed cache filters.
        """
        return list(self.cache_filters or getattr(self, "filterset_fields", []) or [])

    def make_cache_key(self, request):
        """
        Return the cache key for the given request.
        """
        allowed = self.get_cache_filters()
        # collect allowed params; keep multi-valued params as lists
        params = {k: request.GET.getlist(k)
                  for k in allowed if k in request.GET}
        # include page/limit (DRF pagination) and path to avoid cross-view collisions
        page = request.GET.get("page", "")
        page_size = request.GET.get("page_size", "")
        payload = {"path": request.path, "params": params,
                   "page": page, "page_size": page_size}
        s = dumps(payload, sort_keys=True, separators=(",", ":"))
        h = sha256(s.encode()).hexdigest()
        version = ""
        if self.cache_version_key:
            version = str(cache.get(self.cache_version_key) or "")
        return f"fcache:{self.__class__.__name__}:{h}:v={version}"

    def list(self, request, *args, **kwargs):
        """
        Return the list of objects.
        """
        # only apply caching to list() to avoid interfering with other actions
        key = self.make_cache_key(request)
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        response = super().list(request, *args, **kwargs)
        # cache the serialized payload (response.data)
        cache.set(key, response.data, timeout=self.cache_timeout)
        return response
