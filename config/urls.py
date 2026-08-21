from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/account/", include("apps.accounts.urls.user_urls"), name="account"),
    path("api/authenticate/", include("apps.accounts.urls.auth_urls"), name="authenticate"),
    path("api/configuration/", include("apps.accounts.urls.permission_urls"), name="configuration"),
    path("api/settings/", include("apps.settings_app.urls"), name="settings"),
    path("api/nominal-account/", include("apps.accounting.urls"), name="nominal-account"),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
