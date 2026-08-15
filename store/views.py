import json
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.models import BlogPost, Category, Coupon, Order, Product, ProductReview, ReferralCode
from core.models import PIX_DISCOUNT
from store.cart import add_to_cart, clear_cart, get_cart_lines, set_cart, set_cart_qty
from store.checkout_service import OutOfStock, create_order
from store.forms import CheckoutForm, ReferralSignupForm, ReviewForm
from store.whatsapp import whatsapp_url

PRODUCTS_PER_PAGE = 24
FEATURED_LIMIT = 8
RELATED_LIMIT = 4


def _categories_with_totals():
    """So categorias com pelo menos um produto ativo, das mais cheias
    para as mais vazias — clicar numa categoria vazia nao leva a nada util."""
    return Category.objects.annotate(
        total=Count('products', filter=Q(products__active=True))
    ).filter(total__gt=0).order_by('-total', 'name')


def _cart_context(request):
    """Linhas do carrinho com subtotal por item e totais da loja."""
    lines = get_cart_lines(request)
    for line in lines:
        line['subtotal'] = line['price'] * line['qty']
    total = Decimal(str(sum(line['subtotal'] for line in lines)))
    return lines, total


def _keep_referral_cookie(request, response):
    """Grava o cookie de indicacao quando a URL trouxer ?ref=CODIGO valido —
    assim o desconto sobrevive ate o cliente fechar o pedido."""
    code = request.GET.get('ref')
    if code and ReferralCode.objects.filter(code__iexact=code).exists():
        response.set_cookie('ref', code.upper(), max_age=60 * 60 * 24 * 30)
    return response


CATEGORY_SHOWCASE_LIMIT = 8


def _categories_with_sample_photo(limit):
    """As categorias mais cheias, cada uma com uma foto real de produto pra
    servir de capa — em vez de um chip de texto puro."""
    categorias = list(_categories_with_totals()[:limit])
    for categoria in categorias:
        produto = (
            Product.objects.filter(category=categoria, active=True, images__isnull=False)
            .prefetch_related('images')
            .first()
        )
        categoria.sample_image = produto.main_image if produto else None
    return categorias


def home(request):
    response = render(
        request,
        'store/home.html',
        {
            'featured': Product.objects.for_listing().filter(featured=True)[:FEATURED_LIMIT],
            'categories': _categories_with_sample_photo(CATEGORY_SHOWCASE_LIMIT),
            'nav_categories': _categories_with_totals(),
            'total_products': Product.objects.active().count(),
            'inclusive_count': Product.objects.inclusive().count(),
        },
    )
    return _keep_referral_cookie(request, response)


def produtos(request):
    categoria = request.GET.get('categoria')
    busca = request.GET.get('busca', '').strip()
    qs = Product.objects.for_listing()
    if categoria == 'inclusivos':
        qs = qs.filter(is_inclusive=True)
    elif categoria:
        qs = qs.filter(category__slug=categoria)
    if busca:
        qs = qs.filter(
            Q(name__icontains=busca)
            | Q(sku__icontains=busca)
            | Q(brand__name__icontains=busca)
        )
    pagina = Paginator(qs, PRODUCTS_PER_PAGE).get_page(request.GET.get('page'))
    categorias = _categories_with_totals()
    return render(
        request,
        'store/produtos.html',
        {
            'products': pagina.object_list,
            'page_obj': pagina,
            'categories': categorias,
            'nav_categories': categorias,
            'categoria_atual': categoria,
            'busca': busca,
            'total_geral': Product.objects.active().count(),
            'total_inclusivos': Product.objects.inclusive().count(),
        },
    )


def produto_detalhe(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related('images'),
        slug=slug,
        active=True,
    )
    related = (
        Product.objects.for_listing()
        .filter(category=product.category)
        .exclude(id=product.id)[:RELATED_LIMIT]
    )
    variants = list(product.variants.all())
    response = render(
        request,
        'store/produto.html',
        {
            'product': product,
            'related': related,
            'reviews': product.reviews.filter(approved=True),
            'review_form': ReviewForm(),
            'nav_categories': _categories_with_totals(),
            'categoria_atual': product.category.slug,
            'variants_json': json.dumps([
                {'id': v.id, 'label': v.label, 'stock': v.stock} for v in variants
            ]),
        },
    )
    return _keep_referral_cookie(request, response)


@require_POST
def avaliar_produto(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    form = ReviewForm(request.POST)
    if form.is_valid():
        ProductReview.objects.create(
            product=product,
            author_name=form.cleaned_data['author_name'],
            rating=form.cleaned_data['rating'],
            comment=form.cleaned_data['comment'],
        )
        messages.success(request, 'Sua avaliação foi recebida e entra no ar após revisão.')
    else:
        messages.error(request, 'Não foi possível enviar a avaliação. Confira os campos.')
    return redirect('store:produto', slug=slug)


def carrinho(request):
    lines, total = _cart_context(request)
    return render(
        request,
        'store/carrinho.html',
        {
            'lines': lines,
            'total': total,
            'pix_total': (total * (1 - PIX_DISCOUNT)).quantize(Decimal('0.01')),
            'nav_categories': _categories_with_totals(),
        },
    )


@require_POST
def add_cart(request, slug):
    product = get_object_or_404(Product, slug=slug, active=True)
    qty = request.POST.get('qty', 1)
    variant_id = request.POST.get('variant_id') or None
    if variant_id and not product.variants.filter(id=variant_id).exists():
        variant_id = None
    cart = add_to_cart(request, product.id, qty, variant_id=variant_id)
    response = redirect('store:carrinho')
    set_cart(response, cart)
    return response


@require_POST
def update_cart(request, cart_key):
    cart = set_cart_qty(request, cart_key, request.POST.get('qty', 0))
    response = redirect('store:carrinho')
    set_cart(response, cart)
    return response


def _valid_coupon(code):
    if not code:
        return None
    coupon = Coupon.objects.filter(code__iexact=code.strip()).first()
    return coupon if coupon and coupon.is_valid() else None


REFERRAL_COOKIE = 'ref'


def _active_referral(request):
    code = request.GET.get('ref') or request.COOKIES.get(REFERRAL_COOKIE)
    return ReferralCode.objects.filter(code__iexact=code).first() if code else None


def checkout(request):
    lines, total = _cart_context(request)
    if not lines:
        return redirect('store:carrinho')

    erro_estoque = None
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            coupon = _valid_coupon(form.cleaned_data.get('coupon_code'))
            referral = None if coupon else _active_referral(request)
            try:
                order = create_order(
                    request, form.cleaned_data, lines, coupon=coupon, referral=referral
                )
            except OutOfStock as falta:
                erro_estoque = (
                    f'Restam apenas {falta.available} unidades de '
                    f'"{falta.product_name}". Ajuste a quantidade e tente de novo.'
                )
            else:
                response = redirect('store:pedido', code=order.code)
                set_cart(response, clear_cart(request))
                return response
    else:
        form = CheckoutForm()

    return render(
        request,
        'store/checkout.html',
        {
            'lines': lines,
            'total': total,
            'form': form,
            'erro_estoque': erro_estoque,
            'referral_active': _active_referral(request),
            'nav_categories': _categories_with_totals(),
        },
    )


def indicar(request):
    referral = None
    if request.method == 'POST':
        form = ReferralSignupForm(request.POST)
        if form.is_valid():
            referral, _ = ReferralCode.objects.get_or_create(
                owner_email=form.cleaned_data['owner_email'],
                defaults={'owner_name': form.cleaned_data['owner_name']},
            )
    else:
        form = ReferralSignupForm()
    link = request.build_absolute_uri(reverse('store:produtos')) + f'?ref={referral.code}' if referral else None
    return render(
        request,
        'store/indicar.html',
        {'form': form, 'referral': referral, 'link': link, 'nav_categories': _categories_with_totals()},
    )


def blog_lista(request):
    return render(
        request,
        'store/blog_lista.html',
        {'posts': BlogPost.objects.published(), 'nav_categories': _categories_with_totals()},
    )


def blog_post(request, slug):
    post = get_object_or_404(BlogPost.objects.published(), slug=slug)
    return render(
        request,
        'store/blog_post.html',
        {'post': post, 'nav_categories': _categories_with_totals()},
    )


def pedido(request, code):
    order = get_object_or_404(Order.objects.prefetch_related('items'), code=code)
    return render(
        request,
        'store/pedido.html',
        {
            'order': order,
            'whatsapp_url': whatsapp_url(order),
            'nav_categories': _categories_with_totals(),
        },
    )
