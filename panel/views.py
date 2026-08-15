from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Coupon, Order, Product, ProductReview, SiteSettings
from panel.forms import PanelLoginForm, SiteSettingsForm

LOW_STOCK_LIMIT = 4
RECENT_ORDERS_LIMIT = 8
LOW_STOCK_LIST_LIMIT = 6
TOP_PRODUCTS_LIMIT = 5

LOGIN_RATE_LIMIT_MAX_ATTEMPTS = 5
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 5 * 60
LOGIN_RATE_LIMIT_MESSAGE = 'Muitas tentativas, tente novamente em alguns minutos.'

staff_required = user_passes_test(lambda u: u.is_staff, login_url='panel:login')


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _login_attempts_cache_key(request):
    return f'panel_login_attempts:{_client_ip(request)}'


def _is_login_rate_limited(request):
    attempts = cache.get(_login_attempts_cache_key(request), 0)
    return attempts >= LOGIN_RATE_LIMIT_MAX_ATTEMPTS


def _register_failed_login_attempt(request):
    cache_key = _login_attempts_cache_key(request)
    try:
        attempts = cache.incr(cache_key)
    except ValueError:
        attempts = 1
        cache.set(cache_key, attempts, LOGIN_RATE_LIMIT_WINDOW_SECONDS)
    return attempts


def _clear_login_attempts(request):
    cache.delete(_login_attempts_cache_key(request))


def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('panel:dashboard')

    rate_limited = request.method == 'POST' and _is_login_rate_limited(request)
    form = None if rate_limited else PanelLoginForm(request.POST or None)

    if rate_limited:
        form = PanelLoginForm()
        form.add_error(None, LOGIN_RATE_LIMIT_MESSAGE)
        return render(request, 'panel/login.html', {'form': form}, status=429)

    if request.method == 'POST' and form.is_valid():
        _clear_login_attempts(request)
        auth_login(request, form.cleaned_data['user'])
        return redirect(request.GET.get('next') or 'panel:dashboard')

    if request.method == 'POST' and not form.is_valid():
        _register_failed_login_attempt(request)

    return render(request, 'panel/login.html', {'form': form})


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('panel:login')


@login_required(login_url='panel:login')
@staff_required
def dashboard(request):
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    orders_this_month = Order.objects.filter(created_at__gte=month_start)
    revenue = (
        orders_this_month.filter(status__in=Order.PAID_STATUSES).aggregate(Sum('total'))['total__sum']
        or 0
    )
    context = {
        'revenue': revenue,
        'orders_count': orders_this_month.count(),
        'pending_count': Order.objects.filter(status='pendente').count(),
        'recent_orders': Order.objects.all()[:RECENT_ORDERS_LIMIT],
        'low_stock': Product.objects.active().filter(
            stock__gt=0, stock__lte=LOW_STOCK_LIMIT
        ).order_by('stock')[:LOW_STOCK_LIST_LIMIT],
        'pending_reviews': ProductReview.objects.filter(approved=False).count(),
        'active_coupons': Coupon.objects.usable().count(),
        'top_products': Product.objects.active().order_by('-sold_count')[:TOP_PRODUCTS_LIMIT],
    }
    return render(request, 'panel/dashboard.html', context)


@login_required(login_url='panel:login')
@staff_required
def configuracoes(request):
    instance = SiteSettings.objects.filter(pk=1).first()
    if request.method == 'POST':
        form = SiteSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, 'Configurações salvas.')
            return redirect('panel:configuracoes')
    else:
        form = SiteSettingsForm(instance=instance)
    return render(request, 'panel/form.html', {'form': form, 'title': 'Configurações', 'active': 'configuracoes'})
