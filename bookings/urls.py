# apps/bookings/urls.py
from django.urls import path
from django.views.generic import TemplateView

app_name = 'bookings'

urlpatterns = [
    # Placeholder routes; replace with real views later
    path('', TemplateView.as_view(template_name='bookings/home.html'), name='home'),
]
