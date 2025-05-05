from django.urls import path
from . import views 
 
app_name = 'main'

urlpatterns = [
    path('', views.popular_list, name='popular_list'),
    path('shop/', views.product_list, name='product_list'),
    path('shop/<slug:slug>/', views.product_detail,
         name='product_detail'),
    path('shop/category/<slug:category_slug>/', views.product_list,
         name='product_list_by_category'),
    path('about/', views.about, name='about'),  
    path('news/', views.news, name='news'),
    path('dict/', views.dict, name='dict'),
    path('contacts/', views.contacts, name='contacts'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('promocodes/', views.promocodes, name='promocodes'),
    path('reviews/', views.reviews, name='reviews'),
    path('statistics/', views.statistics, name='statistics'),
]