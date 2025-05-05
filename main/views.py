from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category
from cart.forms import CartAddProductForm
from django.shortcuts import render
from django.db.models import Sum, Count, F
from orders.models import Product, Order, OrderItem
from django.contrib.auth.decorators import login_required

def popular_list(request):
   products = Product.objects.filter(available=True)[:3]
   return render(request,
                 'main/index/index.html',
                 {'products' : products})

def product_detail(request, slug):
   product = get_object_or_404(Product, 
                             slug=slug,
                             available=True)
   cart_product_form = CartAddProductForm
   return render(request,
                'main/product/detail.html',
                {'product' : product,
                 'cart_product_form' : cart_product_form}) 

def product_list(request, category_slug=None):
   page = request.GET.get('page', 1) 
   category = None
   categories = Category.objects.all()
   products = Product.objects.filter(available=True)
   paginator = Paginator(products, 5)
   current_page = paginator.page(int(page))
   if category_slug:
      category = get_object_or_404(Category, 
                               slug=category_slug)
      paginator = Paginator(products.filter(category=category), 5)
      current_page = paginator.page(int(page))
      
   return render(request, 
                 'main/product/list.html',
                 {'category': category,
                  'categories' : categories,
                  'products': current_page,
                  'slig_url': category_slug})   

def about(request):
    return render(request, 'main/info/about.html')

def news(request):
    return render(request, 'main/info/news.html')

def dict(request):
    return render(request, 'main/info/dict.html')

def contacts(request):
    return render(request, 'main/info/contacts.html')

def vacancies(request):
    return render(request, 'main/info/vacancies.html')

def promocodes(request):
    return render(request, 'main/info/promocodes.html')

def reviews(request):
    return render(request, 'main/info/reviews.html')


@login_required
def statistics(request):
    total_sales = Order.objects.filter().aggregate(
        total=Sum(F('items__price') * F('items__quantity'))
    )['total'] or 0
    
    total_orders = Order.objects.filter().count()
    
    avg_order = Order.objects.filter().aggregate(
        avg=Sum(F('items__price') * F('items__quantity')) / Count('id')
    )['avg'] or 0
    
    top_products = Product.objects.annotate(
        total_sold=Sum('order_items__quantity')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
    
    profitable_products = Product.objects.annotate(
        revenue=Sum(F('order_items__price') * F('order_items__quantity'))
    ).filter(revenue__gt=0).order_by('-revenue')[:5]
    
    category_stats = Product.objects.values(
        'category__name'
    ).annotate(
        total_sold=Sum('order_items__quantity'),
        total_revenue=Sum(F('order_items__price') * F('order_items__quantity'))
    ).order_by('-total_revenue')
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order': avg_order,
        'top_products': top_products,
        'profitable_products': profitable_products,
        'category_stats': category_stats,
    }
    
    return render(request, 'main/info/statistics.html', context)