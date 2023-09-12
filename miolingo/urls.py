from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from miolingo.core.views import (
    LessonViewset,
    StatViewset,
    TrainingViewset,
    TranslationViewset,
    UserViewset,
)

router = DefaultRouter()
router.register(r"lessons", LessonViewset, basename="lessons")
router.register(r"stats", StatViewset, basename="stats")
router.register(r"trainings", TrainingViewset, basename="trainings")
router.register(r"translations", TranslationViewset, basename="translations")
router.register(r"users", UserViewset, basename="users")

api_urls = router.urls
api_urls += [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
]

if settings.DEBUG:  # pragma: no cover
    # Serve static and media files from development server
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    import debug_toolbar

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    schema_view = get_schema_view(
        openapi.Info(
            title="MioLingo API",
            default_version="v1",
        ),
        public=True,
        permission_classes=[AllowAny],
    )

    urlpatterns += [
        # Debug toolbar
        path("__debug__/", include(debug_toolbar.urls)),
        # DRF login/logout endpoints for session (browsable API, swagger, etc)
        path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        # Swagger and redoc
        path(
            "swagger<format>/",
            schema_view.without_ui(cache_timeout=0),
            name="schema-json",
        ),
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
        ),
    ]

admin.site.site_title = "MioLingo"
admin.site.site_header = "MioLingo"
