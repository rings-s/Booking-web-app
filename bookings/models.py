# apps/bookings/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import uuid
from decimal import Decimal

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='services')
    
    name = models.CharField(_('service name'), max_length=200)
    name_ar = models.CharField(_('service name (Arabic)'), max_length=200, blank=True)
    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'), blank=True)
    
    duration_minutes = models.IntegerField(_('duration (minutes)'))
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(_('discounted price'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Service settings
    max_bookings_per_slot = models.IntegerField(default=1)
    buffer_time_minutes = models.IntegerField(default=0, help_text=_('Buffer time between bookings'))
    requires_deposit = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Availability
    is_active = models.BooleanField(default=True)
    available_days = models.JSONField(default=list)  # List of weekdays
    providers = models.ManyToManyField('businesses.BusinessStaff', blank=True, related_name='services')
    
    # Media
    image = models.ImageField(upload_to='services/', null=True, blank=True)
    
    # Stats
    total_bookings = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        ordering = ['name']
        indexes = [
            models.Index(fields=['business', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.business.name}"
    
    @property
    def current_price(self):
        return self.discounted_price if self.discounted_price else self.price

class TimeSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='time_slots')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='time_slots')
    provider = models.ForeignKey('businesses.BusinessStaff', on_delete=models.SET_NULL, null=True, blank=True)
    
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    is_available = models.BooleanField(default=True)
    max_bookings = models.IntegerField(default=1)
    current_bookings = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Time Slot')
        verbose_name_plural = _('Time Slots')
        ordering = ['date', 'start_time']
        unique_together = ['service', 'provider', 'date', 'start_time']
        indexes = [
            models.Index(fields=['date', 'is_available']),
            models.Index(fields=['service', 'date']),
        ]
    
    def __str__(self):
        return f"{self.service.name} - {self.date} {self.start_time}"
    
    @property
    def is_bookable(self):
        return self.is_available and self.current_bookings < self.max_bookings

class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('CONFIRMED', _('Confirmed')),
        ('IN_PROGRESS', _('In Progress')),
        ('COMPLETED', _('Completed')),
        ('CANCELLED', _('Cancelled')),
        ('NO_SHOW', _('No Show')),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('PARTIALLY_PAID', _('Partially Paid')),
        ('REFUNDED', _('Refunded')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_number = models.CharField(max_length=20, unique=True)
    
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, related_name='bookings')
    
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    provider = models.ForeignKey('businesses.BusinessStaff', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Booking details
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Customer info (for guest bookings or additional info)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_notes = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    
    # Pricing
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Metadata
    source = models.CharField(max_length=50, default='WEBSITE')  # WEBSITE, MOBILE, WALK_IN, PHONE
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='cancelled_bookings')
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Booking')
        verbose_name_plural = _('Bookings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['business', 'date']),
            models.Index(fields=['status', 'date']),
        ]
    
    def __str__(self):
        return f"{self.booking_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.booking_number:
            self.booking_number = self.generate_booking_number()
        super().save(*args, **kwargs)
    
    def generate_booking_number(self):
        from datetime import datetime
        import random
        prefix = 'BK'
        timestamp = datetime.now().strftime('%Y%m%d')
        random_num = random.randint(1000, 9999)
        return f"{prefix}{timestamp}{random_num}"
    
    def calculate_total(self):
        total = self.service_price - self.discount_amount + self.tax_amount
        return max(total, Decimal('0.00'))