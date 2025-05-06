from django.urls import re_path
from . import views

app_name = 'orders'

urlpatterns = [
    re_path(r'^create/$', views.order_create, name='order_create'),
    re_path(r'^created/$', views.order_create, name='order_create')  # Одинаковый view для двух URL
]