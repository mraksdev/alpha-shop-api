from djoser.views import TokenDestroyView as DjoserTokenDestroyView
from drf_spectacular.utils import extend_schema


class TokenDestroyView(DjoserTokenDestroyView):
    """Logout endpoint with a clean OpenAPI schema."""

    serializer_class = None

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        """Remove the current user's authentication token."""
        return super().post(request)
