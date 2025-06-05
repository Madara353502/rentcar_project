from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Booking, Review, Rental, Client
from datetime import date

class BookingForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date < date.today():
                raise forms.ValidationError("Start date cannot be in the past")
            if end_date < start_date:
                raise forms.ValidationError("End date must be after start date")
        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'form-control'}),
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }

class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['start_date', 'days']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
            'days': forms.NumberInput(attrs={'min': 1, 'max': 30})
        }

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date and start_date < timezone.now().date():
            raise ValidationError('Start date cannot be in the past.')
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        days = cleaned_data.get('days')
        
        if start_date and days:
            if days < 1:
                raise ValidationError('Rental period must be at least 1 day.')
            if days > 30:
                raise ValidationError('Maximum rental period is 30 days.')

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['phone', 'address', 'birth_date']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'phone': forms.TextInput(attrs={'placeholder': '+375 (XX) XXX-XX-XX'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        
        # Validate Belarus phone number format
        import re
        pattern = r'^\+375 \((?:29|33|44|25)\) [0-9]{3}-[0-9]{2}-[0-9]{2}$'
        if not re.match(pattern, phone):
            raise ValidationError('Phone number must be in format: +375 (XX) XXX-XX-XX')
        return phone

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            age = (timezone.now().date() - birth_date).days / 365.25
            if age < 18:
                raise forms.ValidationError('You must be at least 18 years old to register.')
        return birth_date 