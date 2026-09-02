import time
from django.utils.deprecation import MiddlewareMixin
from .models import EventLog

class EventLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def process_response(self, request, response):
        if hasattr(request, "user") and request.user.is_authenticated:
            duration = time.time() - getattr(request, "start_time", time.time())
            EventLog.objects.create(
                user=request.user,
                action=f"{request.method} {request.path}",
                description=(
                    f"Vista: {getattr(request.resolver_match, 'view_name', 'desconocida')} | "
                    f"Status: {response.status_code} | "
                    f"Duración: {duration:.3f} segundos"
                ),
            )
        return response