# accounts/urls.py

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_api, name='signup_api'),
    path('login/', views.login_api, name='login_api'),
]
