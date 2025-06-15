from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from functools import wraps

def experiment_mode_required(view_func):
    """Decorator to check if the experiment mode is enabled in settings."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(settings, "EXPERIMENT_MODE", False):
            return Response(
                {"error": "Experiment endpoints are disabled."},
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return _wrapped_view