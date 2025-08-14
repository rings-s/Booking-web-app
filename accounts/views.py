# apps/accounts/views.py
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import CreateView, FormView, TemplateView
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from .models import User
from .forms import SignUpForm, LoginForm, PasswordResetForm, SetNewPasswordForm
import jwt

class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:verify_email_sent')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # Generate verification token
        token = user.generate_verification_token()
        
        # Send verification email
        self.send_verification_email(user, token)
        
        messages.success(self.request, _('Account created successfully! Please check your email to verify your account.'))
        return response
    
    def send_verification_email(self, user, token):
        subject = _('Verify your email - BookingPro')
        verification_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:verify_email', kwargs={'token': token})
        )
        
        html_message = render_to_string('emails/verify_email.html', {
            'user': user,
            'verification_url': verification_url,
        })
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
        )

class LoginView(FormView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('dashboard:home')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)
        
        user = authenticate(self.request, email=email, password=password)
        
        if user is not None:
            if not user.is_verified:
                messages.error(self.request, _('Please verify your email before logging in.'))
                return self.form_invalid(form)
            
            if not user.is_active:
                messages.error(self.request, _('Your account has been deactivated.'))
                return self.form_invalid(form)
            
            login(self.request, user)
            
            # Set session expiry
            if not remember_me:
                self.request.session.set_expiry(0)
            
            # Generate JWT token and store in session
            access_token = user.generate_jwt_token('access')
            refresh_token = user.generate_jwt_token('refresh')
            
            self.request.session['access_token'] = access_token
            self.request.session['refresh_token'] = refresh_token
            
            # Redirect based on user role
            if user.role == 'SUPER_ADMIN':
                return redirect('admin:index')
            elif user.role in ['BUSINESS_ADMIN', 'BUSINESS_STAFF']:
                return redirect('dashboard:business_dashboard')
            else:
                return redirect('dashboard:client_dashboard')
        else:
            messages.error(self.request, _('Invalid email or password.'))
            return self.form_invalid(form)

class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.success(request, _('You have been logged out successfully.'))
        return redirect('accounts:login')

class PasswordResetView(FormView):
    form_class = PasswordResetForm
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_sent')
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            token = user.generate_password_reset_token()
            
            # Send reset email
            self.send_reset_email(user, token)
            
            messages.success(self.request, _('Password reset email sent. Please check your inbox.'))
        except User.DoesNotExist:
            # Don't reveal if email exists
            messages.success(self.request, _('If an account exists with this email, you will receive a password reset link.'))
        
        return super().form_valid(form)
    
    def send_reset_email(self, user, token):
        subject = _('Reset your password - BookingPro')
        reset_url = self.request.build_absolute_uri(
            reverse_lazy('accounts:password_reset_confirm', kwargs={'token': token})
        )
        
        html_message = render_to_string('emails/password_reset.html', {
            'user': user,
            'reset_url': reset_url,
        })
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
        )

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['bookings'] = self.request.user.bookings.all()[:5]
        return context