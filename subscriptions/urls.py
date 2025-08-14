# apps/subscriptions/urls.py
from django.urls import path
from django.views.generic import TemplateView

app_name = 'subscriptions'

urlpatterns = [
    # Placeholder routes; replace with real views later
    path('', TemplateView.as_view(template_name='subscriptions/home.html'), name='home'),
]
