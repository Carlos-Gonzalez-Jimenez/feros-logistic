import hashlib
from typing import Optional, Any

from data_fetcher.global_request_context import get_request
from django.core.cache import cache
from django.utils.translation import get_language_from_request


def update_cache_value(key, value):
    cache.set(key, value)


def set_translatable_cache(key: str, value, lang: str = None, **kwargs):
    lang = get_language_from_request(lang or get_request())
    cache.set(f"{key}.{lang}", value, **kwargs)


def get_translatable_cache(key: str, lang: str = None, **kwargs):
    lang = get_language_from_request(lang or get_request())
    return cache.get(f"{key}.{lang}", **kwargs)


def clear_translatable_cache(key: str, **kwargs):
    cache.delete_pattern(f"{key}.*", **kwargs)


class NomenclatorCacheManager:
    """Manager centralizado para cache de nomencladores"""

    # Tiempo de expiración por defecto (1 hora)
    DEFAULT_TIMEOUT = 3600

    @staticmethod
    def get_cache_key(
            model_name: str, action: str, user=None, pk: Optional[int] = None, **kwargs
    ) -> str:
        """
        Genera clave de cache CONSISTENTE con versión
        """
        user_type = "staff" if user and user.is_staff else "user"
        key_parts = [model_name.lower(), user_type, action]

        if pk:
            key_parts.append(str(pk))

        # Incluir parámetros de paginación y búsqueda para list
        if action == "list":
            page = kwargs.get("page")
            page_size = kwargs.get("page_size")
            search = kwargs.get("search", "")

            if page:
                key_parts.append(f"page_{page}")
            if page_size:
                key_parts.append(f"size_{page_size}")
            if search:
                search_normalized = search.strip().lower()
                search_hash = hashlib.md5(search_normalized.encode()).hexdigest()[:8]
                key_parts.append(f"search_{search_hash}")

        version_key = f"{model_name.lower()}_cache_version"
        current_version = cache.get(version_key, 0)
        key_parts.append(f"v{current_version}")

        return "_".join(key_parts)

    @staticmethod
    def invalidate_model_cache(model_name: str) -> None:
        """
        Invalida cache usando solo sistema de versionado
        Método SIMPLE y EFICIENTE para producción
        """
        model_name_lower = model_name.lower()
        version_key = f"{model_name_lower}_cache_version"

        current_version = cache.get(version_key, 0)
        # Incrementar versión - esto invalida automáticamente todas las claves antiguas
        cache.set(version_key, current_version + 1, timeout=None)

    @staticmethod
    def get_cached_data(
            model_name: str, action: str, user=None, pk: Optional[int] = None, **kwargs
    ) -> Any:
        """
        Obtiene datos del cache
        """
        cache_key = NomenclatorCacheManager.get_cache_key(model_name, action, user, pk, **kwargs)
        return cache.get(cache_key)

    @staticmethod
    def set_cached_data(
            data: Any,
            model_name: str,
            action: str,
            user=None,
            pk: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Guarda datos en cache
        """
        cache_key = NomenclatorCacheManager.get_cache_key(model_name, action, user, pk, **kwargs)

        if timeout is None:
            timeout = NomenclatorCacheManager.DEFAULT_TIMEOUT

        cache.set(cache_key, data, timeout)
        return cache_key
