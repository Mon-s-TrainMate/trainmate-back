# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('sign-up/', views.signup, name='signup'),
    path('login/', views.login_api, name='login_api'),
    path('logout/', views.logout_api, name='logout'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
]
