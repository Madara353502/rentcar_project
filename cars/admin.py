from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.utils import timezone
from .models import (
    CarBodyType, CarBrand, CarModel, CarPark, Car,
    Client, Discount, PenaltyType, Rental, RentalPenalty,
    Promotion, Review, Article, CompanyInfo,
    Employee, Term, Vacancy, PromoCode
)

@admin.register(CarBodyType)
class CarBodyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(CarBrand)
class CarBrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'body_type', 'description')
    list_filter = ('brand', 'body_type')
    search_fields = ('name', 'brand__name', 'description')

@admin.register(CarPark)
class CarParkAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone')
    search_fields = ('name', 'address', 'phone')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'car_model', 'year', 'car_park', 
                   'daily_rental_price', 'is_available', 'display_image')
    list_filter = ('is_available', 'car_model__brand', 'car_park', 'year')
    search_fields = ('license_plate', 'car_model__name', 'car_model__brand__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No image"
    display_image.short_description = 'Image'

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'phone', 'address', 'get_rental_count')
    search_fields = ('user__first_name', 'user__last_name', 'phone', 'address')
    readonly_fields = ('created_at',)

    def get_full_name(self, obj):
        return f"{obj.user.get_full_name()}"
    get_full_name.short_description = 'Full Name'

    def get_rental_count(self, obj):
        return obj.rentals.count()
    get_rental_count.short_description = 'Total Rentals'

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name', 'description')

@admin.register(PenaltyType)
class PenaltyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'description')
    search_fields = ('name', 'description')

class RentalPenaltyInline(admin.TabularInline):
    model = RentalPenalty
    extra = 0

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'client', 'employee', 'start_date', 
                   'expected_return_date', 'actual_return_date', 'status', 
                   'base_price', 'discount_amount', 'total_penalties', 
                   'final_price')
    list_filter = ('status', 'start_date', 'car__car_model__brand')
    search_fields = ('car__license_plate', 'client__user__last_name', 
                    'client__user__first_name')
    readonly_fields = ('created_at', 'updated_at', 'base_price', 
                      'discount_amount', 'total_penalties', 'final_price')
    inlines = [RentalPenaltyInline]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(employee=request.user)
        return qs

@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'updated_at')

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('question', 'created_at')
    search_fields = ('question', 'answer')
    list_filter = ('created_at',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'email', 'phone')
    search_fields = ('name', 'position', 'email')
    list_filter = ('position',)
    ordering = ('order', 'name')

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('is_active', 'created_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('user__username', 'text')
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('code', 'description')
    actions = ['activate_promotions', 'deactivate_promotions']

    def activate_promotions(self, request, queryset):
        queryset.update(is_active=True)
    activate_promotions.short_description = "Activate selected promotions"

    def deactivate_promotions(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_promotions.short_description = "Deactivate selected promotions"

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_until', 'is_active')
    search_fields = ('code', 'description')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    date_hierarchy = 'valid_from' 