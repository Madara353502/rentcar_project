import logging

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Sum, Count, F, Q
from django.contrib.auth.decorators import login_required

from orders.models import Order, OrderItem
from .models import Product, Category
from cart.forms import CartAddProductForm

logger = logging.getLogger(__name__)

def popular_list(request):
    products = Product.objects.filter(available=True)[:5]
    logger.info(f"Displaying popular products: {[p.name for p in products]}")
    return render(request,
                  'main/index/index.html',
                  {'products' : products})

def product_detail(request, slug):
    product = get_object_or_404(Product,
                                     slug=slug,
                                     available=True)
    cart_product_form = CartAddProductForm
    logger.info(f"Displaying details for product '{product.name}' (slug: {slug}).")
    return render(request,
                  'main/product/detail.html',
                  {'product' : product,
                   'cart_product_form' : cart_product_form})

def product_list(request, category_slug=None):
    page = request.GET.get('page', 1)
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'price_asc':
        products = products.order_by('price')
        logger.info("Sorting products by price (ascending).")
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
        logger.info("Sorting products by price (descending).")
    else:
        products = products.order_by('name')
        logger.info("Sorting products by name (default).")

    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        logger.info(f"Filtering products by query: '{query}'. Found {products.count()} results.")

    if category_slug:
        category = get_object_or_404(Category,
                                         slug=category_slug)
        products = products.filter(category=category)
        logger.info(f"Filtering products by category: '{category.name}' (slug: {category_slug}). Found {products.count()} results.")

    paginator = Paginator(products, 5)
    try:
        current_page = paginator.page(int(page))
        logger.info(f"Displaying page {page} of product list. Total pages: {paginator.num_pages}, total products: {paginator.count}.")
    except Exception as e:
        logger.warning(f"Invalid page number '{page}'. Displaying first page. Error: {e}")
        current_page = paginator.page(1)

    return render(request,
                  'main/product/list.html',
                  {'category': category,
                   'categories' : categories,
                   'products': current_page,
                   'slig_url': category_slug,
                   'sort_by': sort_by,
                   'query': query})

def about(request):
    logger.info("Displaying 'About Us' page.")
    return render(request, 'main/info/about.html')

def news(request):
    logger.info("Displaying 'News' page.")
    return render(request, 'main/info/news.html')

def dict(request):
    logger.info("Displaying 'Dictionary' page.")
    return render(request, 'main/info/dict.html')

def contacts(request):
    logger.info("Displaying 'Contacts' page.")
    return render(request, 'main/info/contacts.html')

def vacancies(request):
    logger.info("Displaying 'Vacancies' page.")
    return render(request, 'main/info/vacancies.html')

def promocodes(request):
    logger.info("Displaying 'Promocodes' page.")
    return render(request, 'main/info/promocodes.html')

def reviews(request):
    logger.info("Displaying 'Reviews' page.")
    return render(request, 'main/info/reviews.html')


def statistics(request):
    logger.info("Calculating and displaying statistics.")
    total_sales = Order.objects.filter().aggregate(
        total=Sum(F('items__price') * F('items__quantity'))
    )['total'] or 0
    logger.info(f"Total sales: {total_sales}")

    total_orders = Order.objects.filter().count()
    logger.info(f"Total orders: {total_orders}")

    avg_order = Order.objects.filter().aggregate(
        avg=Sum(F('items__price') * F('items__quantity')) / Count('id')
    )['avg'] or 0
    logger.info(f"Average order value: {avg_order}")

    top_products = Product.objects.annotate(
        total_sold=Sum('order_items__quantity')
    ).filter(total_sold__gt=0).order_by('-total_sold')[:5]
    logger.info(f"Top selling products: {[p.name for p in top_products]}")

    profitable_products = Product.objects.annotate(
        revenue=Sum(F('order_items__price') * F('order_items__quantity'))
    ).filter(revenue__gt=0).order_by('-revenue')[:5]
    logger.info(f"Most profitable products: {[p.name for p in profitable_products]}")

    category_stats = Product.objects.values(
        'category__name'
    ).annotate(
        total_sold=Sum('order_items__quantity'),
        total_revenue=Sum(F('order_items__price') * F('order_items__quantity'))
    ).order_by('-total_revenue')

    total_units = sum(item.get('total_sold', 0) or 0 for item in category_stats) if category_stats else 0
    total_revenue_all = sum(item.get('total_revenue', 0) or 0 for item in category_stats) if category_stats else 0

    for category in category_stats:
        total_sold = category.get('total_sold')
        unit_percentage = (int(total_sold) / total_units * 100) if total_units > 0 and total_sold is not None else 0
        category['unit_percentage'] = unit_percentage

        total_revenue_category = category.get('total_revenue')
        revenue_percentage = (int(total_revenue_category) / total_revenue_all * 100) if total_revenue_all > 0 and total_revenue_category is not None else 0
        category['revenue_percentage'] = revenue_percentage
        logger.info(f"Category '{category['category__name']}': Total sold = {total_sold}, Total revenue = {total_revenue_category}, Unit % = {unit_percentage:.2f}, Revenue % = {revenue_percentage:.2f}")

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'avg_order': avg_order,
        'top_products': top_products,
        'profitable_products': profitable_products,
        'category_stats': list(category_stats),
        'total_units': total_units,
        'total_revenue': total_revenue_all,
    }

    return render(request, 'main/info/statistics.html', context)