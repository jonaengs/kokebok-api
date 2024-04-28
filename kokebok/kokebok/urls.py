from functools import wraps

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest
from django.urls import path
from ninja import NinjaAPI

from core.auth_api import router as auth_router
from recipes.api import router as recipes_router


def require_logged_in(view_func):
    @wraps(view_func)
    def _view_wrapper(request: HttpRequest, *args, **kwargs):
        # TODO: Maybe require is_staff as well?
        if not request.user.is_authenticated:
            return api.create_response(request, {"detail": "Unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)

    return _view_wrapper


api = NinjaAPI(
    # Require login to view api docs in production
    docs_decorator=(lambda x: x)
    if settings.DEBUG
    else require_logged_in,
)
api.add_router("recipes/", recipes_router)
api.add_router("auth/", auth_router)


urlpatterns = [
    path("controls/", admin.site.urls),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
