# dashboard/urls.py
from django.urls import path
from .views import (
    DashboardHomeView,
    CalendarView,
    BookingListView,
)
from django.views.generic import TemplateView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('bookings/', BookingListView.as_view(), name='bookings_list'),

    # Convenience names used in redirects
    path('business/', DashboardHomeView.as_view(), name='business_dashboard'),
    path('client/', DashboardHomeView.as_view(), name='client_dashboard'),
]
