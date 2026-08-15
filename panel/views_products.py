import os
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from PIL import Image, UnidentifiedImageError

from core.models import Brand, Category, Product, ProductImage, Variant
from panel.views import staff_required

IMAGE_ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
IMAGE_MAX_SIZE_BYTES = 5 * 1024 * 1024
MAX_BATCH_FILES = 30


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'sku', 'brand', 'category', 'description',
            'price', 'compare_at_price', 'stock', 'icon',
            'is_inclusive', 'featured', 'active',
        ]


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image', 'alt', 'order']

    def clean_image(self):
        image = self.cleaned_data['image']
        if not _is_valid_image(image):
            raise ValidationError('Imagem invalida: use JPG, PNG ou WEBP de ate 5MB.')
        return image


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['color', 'size', 'sku', 'stock']


@login_required(login_url='panel:login')
@staff_required
def produtos_list(request):
    produtos = Product.objects.select_related('brand', 'category').order_by('-created_at')
    busca = request.GET.get('busca', '').strip()
    categoria_id = request.GET.get('categoria', '').strip()
    marca_id = request.GET.get('marca', '').strip()
    if busca:
        produtos = produtos.filter(name__icontains=busca)
    if categoria_id.isdigit():
        produtos = produtos.filter(category_id=categoria_id)
    if marca_id.isdigit():
        produtos = produtos.filter(brand_id=marca_id)
    return render(
        request,
        'panel/produtos_list.html',
        {
            'active': 'produtos',
            'produtos': produtos,
            'busca': busca,
            'categoria_id': categoria_id,
            'marca_id': marca_id,
            'categories': Category.objects.all(),
            'brands': Brand.objects.all(),
        },
    )


@login_required(login_url='panel:login')
@staff_required
@require_POST
def produto_rapido(request, pk):
    """Edicao rapida de preco e estoque direto na lista — sem abrir a tela
    inteira de edicao. Mantem a busca/filtro atual no redirecionamento."""
    produto = get_object_or_404(Product, pk=pk)
    try:
        price = Decimal(request.POST.get('price', ''))
        stock = int(request.POST.get('stock', ''))
    except (InvalidOperation, ValueError):
        messages.error(request, 'Preço ou estoque inválido — nada foi alterado.')
    else:
        if price < 0 or stock < 0:
            messages.error(request, 'Preço e estoque não podem ser negativos.')
        else:
            produto.price = price
            produto.stock = stock
            produto.save(update_fields=['price', 'stock'])
            messages.success(request, f'{produto.name} atualizado.')

    query = request.META.get('QUERY_STRING', '')
    url = reverse('panel:produtos')
    return redirect(f'{url}?{query}' if query else url)


@login_required(login_url='panel:login')
@staff_required
def produto_novo(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        produto = form.save()
        messages.success(request, 'Produto criado. Agora adicione fotos e variantes.')
        return redirect('panel:produto_editar', pk=produto.pk)
    return render(request, 'panel/produto_form.html', {'active': 'produtos', 'form': form, 'title': 'Novo produto'})


@login_required(login_url='panel:login')
@staff_required
def produto_editar(request, pk):
    produto = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=produto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto atualizado.')
        return redirect('panel:produto_editar', pk=produto.pk)
    return render(
        request,
        'panel/produto_form.html',
        {
            'active': 'produtos',
            'form': form,
            'title': produto.name,
            'produto': produto,
            'image_form': ProductImageForm(),
            'variant_form': VariantForm(),
        },
    )


@login_required(login_url='panel:login')
@staff_required
@require_POST
def produto_remover(request, pk):
    produto = get_object_or_404(Product, pk=pk)
    produto.delete()
    messages.success(request, 'Produto removido.')
    return redirect('panel:produtos')


@login_required(login_url='panel:login')
@staff_required
@require_POST
def produto_foto_nova(request, pk):
    produto = get_object_or_404(Product, pk=pk)
    form = ProductImageForm(request.POST, request.FILES)
    if form.is_valid():
        foto = form.save(commit=False)
        foto.product = produto
        foto.save()
        messages.success(request, 'Foto adicionada.')
    else:
        messages.error(request, 'Não foi possível salvar a foto. Confira o arquivo enviado.')
    return redirect('panel:produto_editar', pk=pk)


@login_required(login_url='panel:login')
@staff_required
@require_POST
def produto_foto_remover(request, pk, image_id):
    produto = get_object_or_404(Product, pk=pk)
    ProductImage.objects.filter(pk=image_id, product=produto).delete()
    messages.success(request, 'Foto removida.')
    return redirect('panel:produto_editar', pk=pk)


@login_required(login_url='panel:login')
@staff_required
@require_POST
def produto_variante_nova(request, pk):
    produto = get_object_or_404(Product, pk=pk)
    form = VariantForm(request.POST)
    if form.is_valid():
        variante = form.save(commit=False)
        variante.product = produto
        variante.save()
        messages.success(request, 'Variante adicionada.')
    else:
        messages.error(request, 'Não foi possível salvar a variante. Confira cor, tamanho e estoque.')
    return redirect('panel:produto_editar', pk=pk)


@login_required(login_url='panel:login')
@staff_required
@require_POST
def produto_variante_remover(request, pk, variant_id):
    produto = get_object_or_404(Product, pk=pk)
    Variant.objects.filter(pk=variant_id, product=produto).delete()
    messages.success(request, 'Variante removida.')
    return redirect('panel:produto_editar', pk=pk)


@login_required(login_url='panel:login')
@staff_required
def produtos_fotos_lote(request):
    """Sobe varias fotos de uma vez. Cada arquivo e associado ao produto cujo
    SKU aparece no nome do arquivo (ex: '1002347.jpg' ou '1002347-frente.jpg').
    Arquivo sem SKU reconhecido nao e salvo e aparece na lista de erros."""
    matched, unmatched, invalid = [], [], []
    if request.method == 'POST':
        skus_by_length = sorted(
            Product.objects.exclude(sku='').values_list('sku', flat=True),
            key=len, reverse=True,
        )
        files = request.FILES.getlist('files')[:MAX_BATCH_FILES]
        for uploaded in files:
            if not _is_valid_image(uploaded):
                invalid.append(uploaded.name)
                continue
            sku = _extract_sku(uploaded.name, skus_by_length)
            if sku is None:
                unmatched.append(uploaded.name)
                continue
            produto = Product.objects.get(sku=sku)
            next_order = (
                ProductImage.objects.filter(product=produto).count()
            )
            ProductImage.objects.create(product=produto, image=uploaded, order=next_order)
            matched.append((uploaded.name, produto.name))

        if matched:
            messages.success(request, f'{len(matched)} foto(s) associada(s) com sucesso.')
        if unmatched:
            messages.error(
                request,
                'Não foi possível associar: ' + ', '.join(unmatched)
                + ' — renomeie o arquivo incluindo o código do produto.',
            )
        if invalid:
            messages.error(
                request,
                'Arquivo(s) rejeitado(s) (formato/tamanho invalido): ' + ', '.join(invalid),
            )

    return render(request, 'panel/produtos_fotos_lote.html', {'active': 'produtos'})


def _extract_sku(filename, known_skus):
    for sku in known_skus:
        if sku in filename:
            return sku
    return None


def _is_valid_image(uploaded):
    ext = os.path.splitext(uploaded.name)[1].lower()
    if ext not in IMAGE_ALLOWED_EXTENSIONS:
        return False
    if uploaded.size > IMAGE_MAX_SIZE_BYTES:
        return False
    try:
        with Image.open(uploaded) as img:
            img.verify()
    except (UnidentifiedImageError, OSError):
        return False
    uploaded.seek(0)
    return True
