from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator, MaxValueValidator
from datetime import date
import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from statistics import median

class CarBodyType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Car Body Type"
        verbose_name_plural = "Car Body Types"

class CarBrand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Car Brand"
        verbose_name_plural = "Car Brands"

class CarModel(models.Model):
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100)
    body_type = models.ForeignKey(CarBodyType, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    class Meta:
        verbose_name = "Car Model"
        verbose_name_plural = "Car Models"
        unique_together = ['brand', 'name']

class CarPark(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Car Park"
        verbose_name_plural = "Car Parks"

class Car(models.Model):
    license_plate = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(regex=r'^[A-Z0-9]+$', message='License plate must contain only uppercase letters and numbers')]
    )
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, related_name='cars')
    car_park = models.ForeignKey(CarPark, on_delete=models.CASCADE, related_name='cars')
    year = models.PositiveIntegerField(validators=[MinValueValidator(1900)])
    car_value = models.DecimalField(max_digits=10, decimal_places=2)
    daily_rental_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='cars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.license_plate} - {self.car_model}"

    class Meta:
        verbose_name = "Car"
        verbose_name_plural = "Cars"

class Client(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+375 \((?:29|33|44|25)\) \d{3}-\d{2}-\d{2}$',
                message="Phone number must be in format: +375 (29) XXX-XX-XX"
            )
        ]
    )
    address = models.TextField()
    birth_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.birth_date:
            age = (timezone.now().date() - self.birth_date).days / 365.25
            if age < 18:
                raise ValidationError('Client must be at least 18 years old.')

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.phone})"

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"

class Discount(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.percentage}%)"

    class Meta:
        verbose_name = "Discount"
        verbose_name_plural = "Discounts"

class PenaltyType(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField()

    def __str__(self):
        return f"{self.name} (${self.amount})"

    class Meta:
        verbose_name = "Penalty Type"
        verbose_name_plural = "Penalty Types"

class Rental(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Active'),
        ('C', 'Completed'),
        ('X', 'Cancelled'),
    ]

    car = models.ForeignKey(Car, on_delete=models.PROTECT, related_name='rentals')
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name='rentals')
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
                               related_name='managed_rentals', limit_choices_to={'is_staff': True})
    start_date = models.DateField()
    days = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.ForeignKey(Discount, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalties = models.ManyToManyField(PenaltyType, through='RentalPenalty')
    total_penalties = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # New rental
            self.base_price = self.car.daily_rental_price * self.days
            if self.discount:
                self.discount_amount = (self.base_price * self.discount.percentage) / 100
            self.final_price = self.base_price - self.discount_amount + self.total_penalties
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rental #{self.pk} - {self.car} by {self.client}"

    class Meta:
        verbose_name = "Rental"
        verbose_name_plural = "Rentals"

class RentalPenalty(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE)
    penalty = models.ForeignKey(PenaltyType, on_delete=models.PROTECT)
    date_applied = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update total penalties in rental
        total = sum(p.penalty.amount for p in self.rental.rentalpenalty_set.all())
        self.rental.total_penalties = total
        self.rental.final_price = self.rental.base_price - self.rental.discount_amount + total
        self.rental.save()

    def __str__(self):
        return f"Penalty {self.penalty} for Rental #{self.rental.pk}"

    class Meta:
        verbose_name = "Rental Penalty"
        verbose_name_plural = "Rental Penalties"
        unique_together = ['rental', 'penalty']

class Promotion(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date must be after start date.')

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.code} ({self.discount_percentage}% off)"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Confirmed'),
        ('A', 'Active'),
        ('F', 'Finished'),
        ('X', 'Cancelled'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} - {self.car} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        if not self.total_price:
            days = (self.end_date - self.start_date).days + 1
            self.total_price = self.car.daily_rental_price * days
        super().save(*args, **kwargs)

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    car = models.ForeignKey('Car', on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.car} ({self.rating}★)"

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.TextField(max_length=500)
    image = models.ImageField(upload_to='articles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class CompanyInfo(models.Model):
    history = models.TextField()
    logo = models.ImageField(upload_to='company/', null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    bank_details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Company Information"

    class Meta:
        verbose_name_plural = "Company Information"

class Term(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

class Employee(models.Model):
    name = models.CharField(max_length=100, default='Employee')
    position = models.CharField(max_length=100, default='Staff')
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} - {self.position}"

    class Meta:
        ordering = ['order']

class Vacancy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    salary_range = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Vacancies"

class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until

class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def end_session(self):
        self.end_time = timezone.now()
        self.duration = self.end_time - self.start_time
        self.save()

    @classmethod
    def get_median_duration(cls, start_date=None, end_date=None):
        queryset = cls.objects.filter(duration__isnull=False)
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__date__lte=end_date)
        
        durations = list(queryset.values_list('duration', flat=True))
        if durations:
            return median(duration.total_seconds() for duration in durations)
        return 0

    def __str__(self):
        return f"{self.user.username} - {self.start_time.date()}" 