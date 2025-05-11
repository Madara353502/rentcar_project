from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category
from cart.forms import CartAddProductForm
from django.shortcuts import render
from django.db.models import Sum, Count, F
from orders.models import Product, Order, OrderItem
from django.contrib.auth.decorators import login_required

def popular_list(request):
   products = Product.objects.filter(available=True)[:5]
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

    total_units = sum(item.get('total_sold', 0) or 0 for item in category_stats) if category_stats else 0
    total_revenue = sum(item.get('total_revenue', 0) or 0 for item in category_stats) if category_stats else 0

    for category in category_stats:
        total_sold = category.get('total_sold')
        unit_percentage = 0
        if total_units > 0:
            if total_sold is not None:
                unit_percentage = (int(total_sold) / total_units * 100)
            else:
                unit_percentage = 0
        category['unit_percentage'] = unit_percentage

        total_revenue_category = category.get('total_revenue')
        revenue_percentage = 0
        if total_revenue > 0:
            if total_revenue_category is not None:
                revenue_percentage = (int(total_revenue_category) / total_revenue * 100)
            else:
                revenue_percentage = 0
        category['revenue_percentage'] = revenue_percentage

    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order': avg_order,
        'top_products': top_products,
        'profitable_products': profitable_products,
        'category_stats': list(category_stats),
        'total_units': total_units,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'main/info/statistics.html', context)