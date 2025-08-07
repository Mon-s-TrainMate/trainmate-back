# trainmate/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('accounts.urls')),
    path('api/members/', include('members.urls')),
    # path('api/records/', include('workouts.urls')),

]

if settings.DEBUG:
    urlpatterns += [
        # API 문서 관련 URL 추가
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'), # OpenAPI JSON/YAML 스키마
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # Swagger UI
        path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'), # ReDoc UI
    ]
