# apps/dashboard/views.py
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from apps.bookings.models import Booking, Service
from apps.businesses.models import Business
from apps.crm.models import Customer, Lead
import json

class BusinessOwnerMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ['BUSINESS_ADMIN', 'BUSINESS_STAFF', 'SUPER_ADMIN']

class DashboardHomeView(BusinessOwnerMixin, TemplateView):
    template_name = 'dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.role == 'BUSINESS_ADMIN':
            business = user.owned_businesses.first()
            if business:
                context.update(self.get_business_stats(business))
        elif user.role == 'CLIENT':
            context.update(self.get_client_stats(user))
        
        return context
    
    def get_business_stats(self, business):
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Today's stats
        today_bookings = Booking.objects.filter(
            business=business,
            date=today
        )
        
        # Monthly stats
        monthly_bookings = Booking.objects.filter(
            business=business,
            date__gte=month_start
        )
        
        # Revenue calculation
        revenue_today = today_bookings.filter(
            payment_status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        revenue_month = monthly_bookings.filter(
            payment_status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Customer stats
        new_customers = Customer.objects.filter(
            business=business,
            created_at__gte=month_start
        ).count()
        
        # Chart data for Plotly
        chart_data = self.get_chart_data(business)
        
        return {
            'business': business,
            'today_bookings': today_bookings.count(),
            'today_revenue': revenue_today,
            'monthly_bookings': monthly_bookings.count(),
            'monthly_revenue': revenue_month,
            'new_customers': new_customers,
            'pending_bookings': today_bookings.filter(status='PENDING').count(),
            'chart_data': json.dumps(chart_data),
            'upcoming_bookings': today_bookings.filter(
                status__in=['PENDING', 'CONFIRMED']
            ).order_by('start_time')[:5],
        }
    
    def get_chart_data(self, business):
        # Last 30 days booking data
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
        
        bookings_by_day = []
        current = start_date
        
        while current <= end_date:
            count = Booking.objects.filter(
                business=business,
                date=current
            ).count()
            bookings_by_day.append({
                'date': current.strftime('%Y-%m-%d'),
                'count': count
            })
            current += timedelta(days=1)
        
        return {
            'bookings_trend': bookings_by_day,
            'services_popularity': self.get_services_popularity(business),
        }
    
    def get_services_popularity(self, business):
        services = Service.objects.filter(business=business).annotate(
            booking_count=Count('bookings')
        ).order_by('-booking_count')[:5]
        
        return [
            {'name': s.name, 'count': s.booking_count}
            for s in services
        ]
    
    def get_client_stats(self, user):
        upcoming_bookings = Booking.objects.filter(
            customer=user,
            date__gte=timezone.now().date(),
            status__in=['PENDING', 'CONFIRMED']
        ).order_by('date', 'start_time')[:5]
        
        past_bookings = Booking.objects.filter(
            customer=user,
            status='COMPLETED'
        ).count()
        
        return {
            'upcoming_bookings': upcoming_bookings,
            'past_bookings': past_bookings,
            'total_bookings': user.bookings.count(),
        }

class CalendarView(BusinessOwnerMixin, TemplateView):
    template_name = 'dashboard/calendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        business = self.get_business()
        
        # Get bookings for calendar
        bookings = Booking.objects.filter(
            business=business,
            date__gte=timezone.now().date() - timedelta(days=30),
            date__lte=timezone.now().date() + timedelta(days=30)
        ).select_related('service', 'customer')
        
        # Format for FullCalendar
        events = []
        for booking in bookings:
            events.append({
                'id': str(booking.id),
                'title': f"{booking.service.name} - {booking.customer_name}",
                'start': f"{booking.date}T{booking.start_time}",
                'end': f"{booking.date}T{booking.end_time}",
                'backgroundColor': self.get_status_color(booking.status),
                'extendedProps': {
                    'status': booking.status,
                    'customer': booking.customer_name,
                    'phone': booking.customer_phone,
                    'service': booking.service.name,
                }
            })
        
        context['events'] = json.dumps(events)
        context['business'] = business
        return context
    
    def get_business(self):
        return self.request.user.owned_businesses.first()
    
    def get_status_color(self, status):
        colors = {
            'PENDING': '#FFA500',
            'CONFIRMED': '#4CAF50',
            'IN_PROGRESS': '#2196F3',
            'COMPLETED': '#9E9E9E',
            'CANCELLED': '#F44336',
            'NO_SHOW': '#795548',
        }
        return colors.get(status, '#607D8B')

class BookingListView(BusinessOwnerMixin, ListView):
    model = Booking
    template_name = 'dashboard/bookings/list.html'
    context_object_name = 'bookings'
    paginate_by = 20
    
    def get_queryset(self):
        business = self.get_business()
        queryset = Booking.objects.filter(business=business)
        
        # Filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(booking_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_email__icontains=search) |
                Q(customer_phone__icontains=search)
            )
        
        return queryset.select_related('service', 'customer').order_by('-created_at')
    
    def get_business(self):
        return self.request.user.owned_businesses.first()