# apps/crm/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid

class Customer(models.Model):
    CUSTOMER_TYPE = [
        ('REGULAR', _('Regular')),
        ('VIP', _('VIP')),
        ('CORPORATE', _('Corporate')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='customers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Customer Info
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE, default='REGULAR')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Additional Info
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)  # For categorization
    
    # Preferences
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_contact_method = models.CharField(max_length=20, default='EMAIL')
    marketing_consent = models.BooleanField(default=False)
    
    # Stats
    total_bookings = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    no_show_count = models.IntegerField(default=0)
    cancellation_count = models.IntegerField(default=0)
    loyalty_points = models.IntegerField(default=0)
    
    # Dates
    first_visit = models.DateTimeField(null=True, blank=True)
    last_visit = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Customer')
        verbose_name_plural = _('Customers')
        ordering = ['-created_at']
        unique_together = ['business', 'email']
        indexes = [
            models.Index(fields=['business', 'customer_type']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.business.name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def calculate_lifetime_value(self):
        return self.total_spent

class Lead(models.Model):
    LEAD_STATUS = [
        ('NEW', _('New')),
        ('CONTACTED', _('Contacted')),
        ('QUALIFIED', _('Qualified')),
        ('PROPOSAL', _('Proposal')),
        ('NEGOTIATION', _('Negotiation')),
        ('CONVERTED', _('Converted')),
        ('LOST', _('Lost')),
    ]
    
    LEAD_SOURCE = [
        ('WEBSITE', _('Website')),
        ('SOCIAL_MEDIA', _('Social Media')),
        ('REFERRAL', _('Referral')),
        ('WALK_IN', _('Walk In')),
        ('PHONE', _('Phone Call')),
        ('EMAIL', _('Email')),
        ('OTHER', _('Other')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE, related_name='leads')
    assigned_to = models.ForeignKey('businesses.BusinessStaff', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Lead Info
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    company = models.CharField(max_length=200, blank=True)
    
    # Lead Details
    status = models.CharField(max_length=20, choices=LEAD_STATUS, default='NEW')
    source = models.CharField(max_length=20, choices=LEAD_SOURCE, default='WEBSITE')
    interested_services = models.ManyToManyField('bookings.Service', blank=True)
    
    # Communication
    notes = models.TextField(blank=True)
    last_contact_date = models.DateTimeField(null=True, blank=True)
    next_followup_date = models.DateTimeField(null=True, blank=True)
    
    # Conversion
    converted = models.BooleanField(default=False)
    converted_date = models.DateTimeField(null=True, blank=True)
    converted_customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Value
    estimated_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    probability = models.IntegerField(default=0, help_text="Probability of conversion (0-100)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Lead')
        verbose_name_plural = _('Leads')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business', 'status']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.business.name}"

class Communication(models.Model):
    COMM_TYPE = [
        ('EMAIL', _('Email')),
        ('PHONE', _('Phone')),
        ('SMS', _('SMS')),
        ('MEETING', _('Meeting')),
        ('NOTE', _('Note')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey('businesses.Business', on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, null=True, blank=True, related_name='communications')
    
    type = models.CharField(max_length=20, choices=COMM_TYPE)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Communication')
        verbose_name_plural = _('Communications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type} - {self.subject}"