from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use Agg backend
import io
import base64
from .models import (
    CarBodyType, CarBrand, CarModel, CarPark, Car,
    Client, Discount, PenaltyType, Rental, RentalPenalty,
    Promotion, Review, UserSession, Article, PromoCode, CompanyInfo,
    Employee, Term, Vacancy
)
from .forms import RentalForm, ClientForm, ReviewForm

def is_staff_user(user):
    return user.is_staff

def home(request):
    available_cars = Car.objects.filter(is_available=True)[:6]
    latest_article = Article.objects.filter(created_at__lte=timezone.now()).first()
    active_promotions = PromoCode.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    )[:3]
    
    return render(request, 'cars/home.html', {
        'available_cars': available_cars,
        'latest_article': latest_article,
        'active_promotions': active_promotions,
    })

def about(request):
    company_info = CompanyInfo.objects.first()
    return render(request, 'cars/about.html', {
        'company_info': company_info
    })

def news_list(request):
    articles = Article.objects.all()
    return render(request, 'cars/news_list.html', {
        'articles': articles
    })

def news_detail(request, pk):
    article = get_object_or_404(Article, pk=pk)
    return render(request, 'cars/news_detail.html', {
        'article': article
    })

def terms(request):
    terms_list = Term.objects.all()
    return render(request, 'cars/terms.html', {
        'terms': terms_list
    })

def contacts(request):
    employees = Employee.objects.all()
    return render(request, 'cars/contacts.html', {
        'employees': employees
    })

def privacy_policy(request):
    return render(request, 'cars/privacy_policy.html')

def vacancies(request):
    active_vacancies = Vacancy.objects.filter(is_active=True)
    return render(request, 'cars/vacancies.html', {
        'vacancies': active_vacancies
    })

def reviews(request):
    reviews_list = Review.objects.all()
    return render(request, 'cars/reviews.html', {
        'reviews': reviews_list
    })

@login_required
def add_review(request):
    car_id = request.GET.get('car_id')
    car = None
    if car_id:
        car = get_object_or_404(Car, id=car_id)
    else:
        messages.error(request, 'Please select a car to review.')
        return redirect('car_list')

    if request.method == 'POST':
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        
        if rating and text:
            Review.objects.create(
                user=request.user,
                car=car,
                rating=rating,
                text=text
            )
            messages.success(request, 'Thank you for your review!')
            return redirect('car_detail', car_id=car.id)
            
    return render(request, 'cars/add_review.html', {'car': car})

@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    
    # Check if the user is the owner of the review
    if review.user != request.user:
        messages.error(request, 'You can only delete your own reviews.')
        return redirect('reviews')
    
    if request.method == 'POST':
        car_id = review.car.id
        review.delete()
        messages.success(request, 'Your review has been deleted successfully.')
        return redirect('car_detail', car_id=car_id)
    
    return render(request, 'cars/delete_review_confirm.html', {'review': review})

def promotions(request):
    active_promos = PromoCode.objects.filter(
        is_active=True,
        valid_from__lte=timezone.now(),
        valid_until__gte=timezone.now()
    )
    archived_promos = PromoCode.objects.filter(
        Q(valid_until__lt=timezone.now()) | Q(is_active=False)
    )
    return render(request, 'cars/promotions.html', {
        'active_promos': active_promos,
        'archived_promos': archived_promos
    })

def car_list(request):
    cars = Car.objects.all()
    show_all = request.GET.get('show_all', '0') == '1'
    
    # Filter available cars
    if not show_all:
        cars = cars.filter(is_available=True)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        cars = cars.filter(
            Q(car_model__brand__name__icontains=search_query) |
            Q(car_model__name__icontains=search_query) |
            Q(license_plate__icontains=search_query)
        )
    
    # Filtering
    brand = request.GET.get('brand')
    body_type = request.GET.get('body_type')
    year_from = request.GET.get('year_from')
    year_to = request.GET.get('year_to')
    price_from = request.GET.get('price_from')
    price_to = request.GET.get('price_to')
    
    if brand:
        cars = cars.filter(car_model__brand__id=brand)
    if body_type:
        cars = cars.filter(car_model__body_type__id=body_type)
    if year_from:
        cars = cars.filter(year__gte=year_from)
    if year_to:
        cars = cars.filter(year__lte=year_to)
    if price_from:
        cars = cars.filter(daily_rental_price__gte=price_from)
    if price_to:
        cars = cars.filter(daily_rental_price__lte=price_to)
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    cars = cars.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(cars, 9)
    page = request.GET.get('page')
    cars = paginator.get_page(page)
    
    # Get filter options for template
    brands = CarBrand.objects.all()
    body_types = CarBodyType.objects.all()
    
    context = {
        'cars': cars,
        'brands': brands,
        'body_types': body_types,
        'search_query': search_query,
        'current_sort': sort_by,
        'show_all': show_all,
        'selected_filters': {
            'brand': brand,
            'body_type': body_type,
            'year_from': year_from,
            'year_to': year_to,
            'price_from': price_from,
            'price_to': price_to,
        }
    }
    return render(request, 'cars/car_list.html', context)

def car_detail(request, car_id):
    car = get_object_or_404(Car.objects.select_related(
        'car_model',
        'car_model__brand',
        'car_model__body_type',
        'car_park'
    ).prefetch_related('reviews'), id=car_id)
    
    # Check if the current user has already reviewed this car
    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(car=car, user=request.user).exists()
    
    return render(request, 'cars/car_detail.html', {
        'car': car,
        'has_reviewed': has_reviewed,
    })

@login_required
def rent_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    if not car.is_available:
        messages.error(request, 'This car is not available for rent.')
        return redirect('car_detail', car_id=car_id)
    
    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            rental = form.save(commit=False)
            rental.car = car
            rental.client = request.user.client
            
            # If user is staff, use them as employee, otherwise get first available staff user
            if request.user.is_staff:
                rental.employee = request.user
            else:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                default_employee = User.objects.filter(is_staff=True).first()
                if not default_employee:
                    messages.error(request, 'No staff members available to process the rental.')
                    return redirect('car_detail', car_id=car_id)
                rental.employee = default_employee
            
            # Calculate expected return date
            rental.expected_return_date = rental.start_date + timedelta(days=rental.days)
            
            # Calculate prices
            rental.base_price = car.daily_rental_price * rental.days
            rental.final_price = rental.base_price
            
            rental.save()
            
            car.is_available = False
            car.save()
            
            messages.success(request, 'Car rental request submitted successfully.')
            return redirect('rental_detail', rental_id=rental.id)
    else:
        form = RentalForm()
    
    return render(request, 'cars/rent_car.html', {
        'form': form,
        'car': car
    })

@login_required
def rental_detail(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    # Check if the user is authorized to view this rental
    if not request.user.is_staff and rental.client.user != request.user:
        messages.error(request, 'You are not authorized to view this rental.')
        return redirect('my_rentals')
    return render(request, 'cars/rental_detail.html', {'rental': rental})

@login_required
def my_rentals(request):
    rentals = Rental.objects.filter(client__user=request.user).order_by('-created_at')
    return render(request, 'cars/my_rentals.html', {'rentals': rentals})

@login_required
@user_passes_test(is_staff_user)
def manage_rentals(request):
    status_filter = request.GET.get('status', '')
    rentals = Rental.objects.all()
    
    if status_filter:
        rentals = rentals.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        rentals = rentals.filter(
            Q(client__user__first_name__icontains=search_query) |
            Q(client__user__last_name__icontains=search_query) |
            Q(car__license_plate__icontains=search_query)
        )
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    rentals = rentals.order_by(sort_by)
    
    # Pagination for rentals
    paginator = Paginator(rentals, 20)
    page = request.GET.get('page')
    rentals = paginator.get_page(page)
    
    context = {
        'rentals': rentals,
        'status_filter': status_filter,
        'search_query': search_query,
        'current_sort': sort_by
    }
    return render(request, 'cars/manage_rentals.html', context)


@login_required
def profile(request):
    try:
        client = request.user.client
    except Client.DoesNotExist:
        client = None
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.user = request.user
            client.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ClientForm(instance=client)
    
    return render(request, 'cars/profile.html', {'form': form})

@user_passes_test(is_staff_user)
def statistics(request):
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30) 
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get basic statistics
    rentals = Rental.objects.filter(created_at__date__range=[start_date, end_date])
    total_rentals = rentals.count()
    total_revenue = rentals.aggregate(Sum('final_price'))['final_price__sum'] or 0
    avg_rental_duration = rentals.aggregate(Avg('days'))['days__avg'] or 0
    
    # Get popular cars data
    popular_cars = Car.objects.annotate(
        rental_count=Count('rentals', filter=Q(
            rentals__created_at__date__range=[start_date, end_date]
        ))
    ).order_by('-rental_count')[:5]
    
    # Get brand revenue data
    brand_revenue = CarBrand.objects.annotate(
        revenue=Sum('models__cars__rentals__final_price', filter=Q(
            models__cars__rentals__created_at__date__range=[start_date, end_date]
        ))
    ).filter(revenue__gt=0).order_by('-revenue')

    # Generate popular cars chart
    plt.figure(figsize=(10, 6))
    plt.clf()
    car_names = [f"{car.car_model.brand.name} {car.car_model.name}" for car in popular_cars]
    rental_counts = [car.rental_count for car in popular_cars]
    plt.bar(car_names, rental_counts)
    plt.xticks(rotation=45, ha='right')
    plt.title('Most Popular Cars')
    plt.xlabel('Cars')
    plt.ylabel('Number of Rentals')
    plt.tight_layout()
    
    # Save popular cars chart to buffer
    popular_cars_buffer = io.BytesIO()
    plt.savefig(popular_cars_buffer, format='png')
    popular_cars_buffer.seek(0)
    popular_cars_chart = base64.b64encode(popular_cars_buffer.getvalue()).decode()
    plt.close()

    # Generate brand revenue chart
    plt.figure(figsize=(10, 6))
    plt.clf()
    brand_names = [brand.name for brand in brand_revenue]
    revenues = [float(brand.revenue) for brand in brand_revenue]
    plt.pie(revenues, labels=brand_names, autopct='%1.1f%%')
    plt.title('Revenue by Brand')
    plt.axis('equal')
    plt.tight_layout()
    
    # Save brand revenue chart to buffer
    brand_revenue_buffer = io.BytesIO()
    plt.savefig(brand_revenue_buffer, format='png')
    brand_revenue_buffer.seek(0)
    brand_revenue_chart = base64.b64encode(brand_revenue_buffer.getvalue()).decode()
    plt.close()
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_rentals': total_rentals,
        'total_revenue': total_revenue,
        'avg_rental_duration': round(avg_rental_duration, 1),
        'popular_cars': popular_cars,
        'brand_revenue': brand_revenue,
        'popular_cars_chart': popular_cars_chart,
        'brand_revenue_chart': brand_revenue_chart
    }
    return render(request, 'cars/statistics.html', context)

@login_required
def cancel_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    
   
    if not request.user.is_staff and rental.client.user != request.user:
        messages.error(request, 'You are not authorized to cancel this rental.')
        return redirect('my_rentals')
    
    
    if rental.status != 'P':
        messages.error(request, 'Only pending rentals can be cancelled.')
        return redirect('rental_detail', rental_id=rental.id)
    
    rental.status = 'X'
    rental.car.is_available = True
    rental.car.save()
    rental.save()
    
    messages.success(request, 'Rental cancelled successfully.')
    return redirect('my_rentals')

@user_passes_test(is_staff_user)
def approve_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    
   
    if rental.status != 'P':
        messages.error(request, 'Only pending rentals can be approved.')
        return redirect('rental_detail', rental_id=rental.id)
    
    rental.status = 'A'
    rental.save()
    
    messages.success(request, 'Rental approved successfully.')
    return redirect('manage_rentals')

@user_passes_test(is_staff_user)
def complete_rental(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    
    
    if rental.status != 'A':
        messages.error(request, 'Only active rentals can be marked as completed.')
        return redirect('rental_detail', rental_id=rental.id)
    
    rental.status = 'C'
    rental.actual_return_date = timezone.now().date()
    rental.car.is_available = True
    rental.car.save()
    rental.save()
    
    messages.success(request, 'Rental marked as completed successfully.')
    return redirect('manage_rentals')

@user_passes_test(is_staff_user)
def add_penalty(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id)
    
    if request.method == 'POST':
        penalty_type = get_object_or_404(PenaltyType, id=request.POST.get('penalty_type'))
        notes = request.POST.get('notes', '')
        
        RentalPenalty.objects.create(
            rental=rental,
            penalty=penalty_type,
            notes=notes
        )
        
        messages.success(request, 'Penalty added successfully.')
        return redirect('rental_detail', rental_id=rental.id)
    
    penalty_types = PenaltyType.objects.all()
    return render(request, 'cars/add_penalty.html', {
        'rental': rental,
        'penalty_types': penalty_types
    })

@login_required
def submit_review(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    
    # Check if user has already reviewed this car
    if Review.objects.filter(car=car, user=request.user).exists():
        messages.error(request, 'You have already reviewed this car.')
        return redirect('car_detail', car_id=car_id)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.car = car
            review.user = request.user
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('car_detail', car_id=car_id)
    else:
        form = ReviewForm()
    
    return render(request, 'cars/submit_review.html', {
        'form': form,
        'car': car
    }) 