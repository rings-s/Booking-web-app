# apps/businesses/urls.py
from django.urls import path
from django.views.generic import TemplateView

app_name = 'businesses'

urlpatterns = [
    # Placeholder routes; replace with real views later
    path('', TemplateView.as_view(template_name='businesses/home.html'), name='home'),
]
