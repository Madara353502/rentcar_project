from django.urls import path
from . import views

urlpatterns = [
    # Public URLs
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('news/', views.news_list, name='news_list'),
    path('news/<int:pk>/', views.news_detail, name='news_detail'),
    path('terms/', views.terms, name='terms'),
    path('contacts/', views.contacts, name='contacts'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    path('reviews/add/', views.add_review, name='add_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('promotions/', views.promotions, name='promotions'),
    path('cars/', views.car_list, name='car_list'),
    path('cars/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/<int:car_id>/rent/', views.rent_car, name='rent_car'),
    path('cars/<int:car_id>/review/', views.submit_review, name='submit_review'),
    
    # Authentication required URLs
    path('rentals/', views.my_rentals, name='my_rentals'),
    path('rentals/<int:rental_id>/', views.rental_detail, name='rental_detail'),
    path('rentals/<int:rental_id>/cancel/', views.cancel_rental, name='cancel_rental'),
    path('profile/', views.profile, name='profile'),
    
    # Staff only URLs
    path('manage/rentals/', views.manage_rentals, name='manage_rentals'),
    path('rentals/<int:rental_id>/approve/', views.approve_rental, name='approve_rental'),
    path('rentals/<int:rental_id>/complete/', views.complete_rental, name='complete_rental'),
    path('rentals/<int:rental_id>/add-penalty/', views.add_penalty, name='add_penalty'),
    path('statistics/', views.statistics, name='statistics'),
] 