# apps/subscriptions/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid
from datetime import timedelta
from django.utils import timezone

class Plan(models.Model):
    BILLING_PERIOD = [
        ('MONTHLY', _('Monthly')),
        ('QUARTERLY', _('Quarterly')),
        ('YEARLY', _('Yearly')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('plan name'), max_length=100)
    name_ar = models.CharField(_('plan name (Arabic)'), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_('description'))
    description_ar = models.TextField(_('description (Arabic)'))
    
    # Pricing
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIOD)
    trial_days = models.IntegerField(default=0)
    
    # Features
    features = models.JSONField(default=dict)  # JSON with feature flags
    max_businesses = models.IntegerField(default=1)
    max_staff = models.IntegerField(default=5)
    max_services = models.IntegerField(default=10)
    max_bookings_per_month = models.IntegerField(default=100)
    
    # Feature Flags
    has_crm = models.BooleanField(default=True)
    has_analytics = models.BooleanField(default=True)
    has_email_reminders = models.BooleanField(default=True)
    has_sms_reminders = models.BooleanField(default=False)
    has_online_payments = models.BooleanField(default=False)
    has_custom_branding = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)
    
    # Display
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Plan')
        verbose_name_plural = _('Plans')
        ordering = ['order', 'price']
    
    def __str__(self):
        return f"{self.name} - {self.get_billing_period_display()}"
    
    def get_period_days(self):
        if self.billing_period == 'MONTHLY':
            return 30
        elif self.billing_period == 'QUARTERLY':
            return 90
        elif self.billing_period == 'YEARLY':
            return 365
        return 30

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('TRIAL', _('Trial')),
        ('ACTIVE', _('Active')),
        ('PAST_DUE', _('Past Due')),
        ('CANCELLED', _('Cancelled')),
        ('EXPIRED', _('Expired')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.OneToOneField('businesses.Business', on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TRIAL')
    
    # Dates
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    trial_end_date = models.DateTimeField(null=True, blank=True)
    
    # Billing
    next_billing_date = models.DateTimeField()
    last_payment_date = models.DateTimeField(null=True, blank=True)
    last_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Usage
    current_month_bookings = models.IntegerField(default=0)
    total_bookings = models.IntegerField(default=0)
    
    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.business.name} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.get_period_days())
        if not self.next_billing_date:
            self.next_billing_date = self.end_date
        if self.plan.trial_days > 0 and not self.trial_end_date:
            self.trial_end_date = self.start_date + timedelta(days=self.plan.trial_days)
        super().save(*args, **kwargs)
    
    def is_active(self):
        return self.status in ['TRIAL', 'ACTIVE'] and self.end_date > timezone.now()
    
    def can_add_booking(self):
        if self.plan.max_bookings_per_month == -1:  # Unlimited
            return True
        return self.current_month_bookings < self.plan.max_bookings_per_month