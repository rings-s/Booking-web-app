# apps/accounts/urls.py
from django.urls import path
from django.views.generic import TemplateView
from .views import (
    SignUpView,
    LoginView,
    LogoutView,
    PasswordResetView,
    ProfileView,
)

app_name = 'accounts'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('profile/', ProfileView.as_view(), name='profile'),

    # Placeholder routes for flows referenced in views/emails
    path('verify-email/<str:token>/', TemplateView.as_view(template_name='accounts/verify_email.html'), name='verify_email'),
    path('verify-email/sent/', TemplateView.as_view(template_name='accounts/verify_email_sent.html'), name='verify_email_sent'),
    path('password-reset/sent/', TemplateView.as_view(template_name='accounts/password_reset_sent.html'), name='password_reset_sent'),
    path('password-reset/confirm/<str:token>/', TemplateView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
]
