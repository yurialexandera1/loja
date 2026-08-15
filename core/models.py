from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

PIX_DISCOUNT = Decimal('0.03')
LOW_STOCK_THRESHOLD = 4
CENTS = Decimal('0.01')


class Category(models.Model):
    name = models.CharField('nome', max_length=120)
    slug = models.SlugField(unique=True)
    icon = models.CharField('icone', max_length=40, default='tag')
    order = models.PositiveIntegerField('ordem', default=0)
    seo_text = models.TextField(
        'texto de SEO',
        blank=True,
        default='',
        help_text='Paragrafo exibido no topo da categoria, para busca organica.',
    )

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField('nome', max_length=120)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)

    def inclusive(self):
        return self.active().filter(is_inclusive=True)

    def for_listing(self):
        return self.active().select_related('category', 'brand').prefetch_related('images')


class Product(models.Model):
    name = models.CharField('nome', max_length=200)
    slug = models.SlugField(unique=True)
    sku = models.CharField('codigo', max_length=40, blank=True, default='', db_index=True)
    description = models.TextField('descricao', blank=True)
    price = models.DecimalField('preco', max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(
        'preco de',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Preco anterior, exibido riscado. Deixe vazio se nao houver desconto.',
    )
    stock = models.PositiveIntegerField('estoque', default=0)
    icon = models.CharField('icone', max_length=40, default='package')
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='categoria',
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='marca',
    )
    is_inclusive = models.BooleanField(
        'linha inclusiva',
        default=False,
        help_text='Marque para exibir o selo e listar na vitrine inclusiva.',
    )
    active = models.BooleanField('ativo', default=True)
    featured = models.BooleanField('destaque', default=False)
    sold_count = models.PositiveIntegerField('vendidos', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        constraints = [
            models.UniqueConstraint(
                fields=['sku'],
                condition=~models.Q(sku=''),
                name='unique_sku_when_filled',
            )
        ]
        indexes = [
            models.Index(fields=['active', 'category']),
            models.Index(fields=['active', 'is_inclusive']),
            models.Index(fields=['active', '-created_at']),
            models.Index(fields=['featured']),
        ]

    def __str__(self):
        return self.name

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_low_stock(self):
        return 0 < self.stock <= LOW_STOCK_THRESHOLD

    @property
    def has_discount(self):
        return bool(self.compare_at_price and self.compare_at_price > self.price)

    @property
    def discount_percent(self):
        if not self.has_discount:
            return 0
        return int((self.compare_at_price - self.price) / self.compare_at_price * 100)

    @property
    def pix_price(self):
        return (self.price * (1 - PIX_DISCOUNT)).quantize(CENTS, rounding=ROUND_HALF_UP)

    @property
    def main_image(self):
        return self.images.first()

    @property
    def total_variant_stock(self):
        total = self.variants.aggregate(models.Sum('stock'))['stock__sum']
        return total if total is not None else self.stock

    @property
    def average_rating(self):
        result = self.reviews.filter(approved=True).aggregate(models.Avg('rating'))['rating__avg']
        return round(result, 1) if result is not None else None

    @property
    def review_count(self):
        return self.reviews.filter(approved=True).count()


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images', verbose_name='produto'
    )
    image = models.ImageField('imagem', upload_to='produtos/')
    alt = models.CharField(
        'texto alternativo',
        max_length=200,
        blank=True,
        default='',
        help_text='Descreva a foto para quem usa leitor de tela.',
    )
    order = models.PositiveIntegerField('ordem', default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Foto do produto'
        verbose_name_plural = 'Fotos do produto'

    def __str__(self):
        return f'{self.product.name} #{self.order}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
        ('enviado', 'Enviado'),
        ('entregue', 'Entregue'),
        ('cancelado', 'Cancelado'),
    ]
    PAID_STATUSES = ['pago', 'enviado', 'entregue']

    code = models.CharField('codigo', max_length=32, unique=True)
    customer_name = models.CharField('cliente', max_length=200)
    email = models.EmailField('e-mail')
    phone = models.CharField('telefone', max_length=40, blank=True)
    address = models.CharField('endereco', max_length=300)
    city = models.CharField('cidade', max_length=120)
    zip = models.CharField('cep', max_length=20)
    shipping_option = models.CharField('frete', max_length=40, default='padrao')
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders',
        verbose_name='cupom',
    )
    discount = models.DecimalField('desconto', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('total', max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        'status', max_length=20, choices=STATUS_CHOICES, default='pendente'
    )
    whatsapp_sent_at = models.DateTimeField('enviado no whatsapp', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        indexes = [models.Index(fields=['status', '-created_at'])]

    def __str__(self):
        return f'{self.code} — {self.customer_name}'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items', verbose_name='pedido'
    )
    product_name = models.CharField('produto', max_length=200)
    sku = models.CharField('codigo', max_length=40, blank=True, default='')
    icon = models.CharField('icone', max_length=40, default='package')
    price = models.DecimalField('preco', max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField('quantidade', default=1)

    class Meta:
        verbose_name = 'Item do pedido'
        verbose_name_plural = 'Itens do pedido'

    def __str__(self):
        return f'{self.qty}x {self.product_name}'

    @property
    def subtotal(self):
        return self.price * self.qty


class CouponQuerySet(models.QuerySet):
    def usable(self):
        return self.filter(active=True)


class Coupon(models.Model):
    code = models.CharField('codigo', max_length=32, unique=True)
    percent_off = models.PositiveIntegerField(
        'desconto (%)',
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='De 1 a 100. Aplicado sobre o subtotal, antes do frete.',
    )
    active = models.BooleanField('ativo', default=True)
    expires_at = models.DateTimeField('expira em', null=True, blank=True)
    max_uses = models.PositiveIntegerField(
        'limite de usos', null=True, blank=True, help_text='Deixe vazio para uso ilimitado.'
    )
    used_count = models.PositiveIntegerField('vezes usado', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = CouponQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Cupom'
        verbose_name_plural = 'Cupons'

    def __str__(self):
        return f'{self.code} (-{self.percent_off}%)'

    def is_valid(self):
        if not self.active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    def discount_for(self, subtotal):
        raw = (subtotal * self.percent_off / 100).quantize(CENTS, rounding=ROUND_HALF_UP)
        return min(raw, subtotal)


class ProductReview(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='produto'
    )
    author_name = models.CharField('nome', max_length=120)
    rating = models.PositiveSmallIntegerField(
        'nota', validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField('comentario')
    approved = models.BooleanField(
        'aprovado',
        default=False,
        help_text='So avaliacoes aprovadas aparecem na loja e contam na nota media.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Avaliacao'
        verbose_name_plural = 'Avaliacoes'
        indexes = [
            models.Index(fields=['product', 'approved']),
        ]

    def __str__(self):
        return f'{self.product.name} — {self.rating}/5 por {self.author_name}'


class BlogPostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(published=True)


class BlogPost(models.Model):
    title = models.CharField('titulo', max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.CharField(
        'resumo', max_length=300, blank=True, default='',
        help_text='Aparece na listagem e como meta description.',
    )
    body = models.TextField('conteudo')
    cover_icon = models.CharField('icone de capa', max_length=40, default='package')
    published = models.BooleanField('publicado', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = BlogPostQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Artigo'
        verbose_name_plural = 'Artigos'

    def __str__(self):
        return self.title


class Variant(models.Model):
    """Estoque por combinacao de cor/tamanho, separado do estoque do produto base.
    Um produto que usa variantes ignora Product.stock — a soma das variantes manda."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='variants', verbose_name='produto'
    )
    color = models.CharField('cor', max_length=60, blank=True, default='')
    size = models.CharField('tamanho', max_length=60, blank=True, default='')
    sku = models.CharField('codigo', max_length=40, blank=True, default='')
    stock = models.PositiveIntegerField('estoque', default=0)

    class Meta:
        ordering = ['color', 'size']
        verbose_name = 'Variante'
        verbose_name_plural = 'Variantes'
        constraints = [
            models.UniqueConstraint(fields=['product', 'color', 'size'], name='unique_variant_per_product')
        ]

    def __str__(self):
        return f'{self.product.name} — {self.label}'

    @property
    def label(self):
        return ' · '.join(part for part in [self.color, self.size] if part)

    @property
    def in_stock(self):
        return self.stock > 0


def _generate_referral_code():
    import secrets
    import string

    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = 'CS' + ''.join(secrets.choice(alphabet) for _ in range(6))
        if not ReferralCode.objects.filter(code=code).exists():
            return code


class ReferralCode(models.Model):
    """Codigo de indicacao: quem indica ganha recompensa apos N indicacoes usadas."""

    code = models.CharField('codigo', max_length=16, unique=True, editable=False)
    owner_name = models.CharField('nome de quem indica', max_length=200)
    owner_email = models.EmailField('e-mail de quem indica')
    reward_threshold = models.PositiveIntegerField(
        'indicacoes para ganhar recompensa', default=3
    )
    uses = models.PositiveIntegerField('vezes usado', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Codigo de indicacao'
        verbose_name_plural = 'Codigos de indicacao'

    def __str__(self):
        return f'{self.code} — {self.owner_name}'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = _generate_referral_code()
        super().save(*args, **kwargs)

    def register_use(self):
        self.uses = models.F('uses') + 1
        self.save(update_fields=['uses'])
        self.refresh_from_db(fields=['uses'])

    @property
    def reward_unlocked(self):
        return self.uses >= self.reward_threshold


class ShippingZoneQuerySet(models.QuerySet):
    def for_cep(self, cep):
        digits = ''.join(ch for ch in cep if ch.isdigit()).ljust(8, '0')[:8]
        candidates = self.filter(active=True, cep_start__lte=digits, cep_end__gte=digits)
        return min(
            candidates, key=lambda zone: int(zone.cep_end) - int(zone.cep_start), default=None
        )


class ShippingZone(models.Model):
    """Faixa de CEP com preco e prazo proprios — aproximacao gratuita sem contrato
    com os Correios. Zonas mais estreitas (raio menor) vencem em caso de sobreposicao."""

    name = models.CharField('nome', max_length=120)
    cep_start = models.CharField(
        'cep inicial', max_length=8, validators=[RegexValidator(r'^\d{8}$', 'Use 8 digitos, sem hifen.')]
    )
    cep_end = models.CharField(
        'cep final', max_length=8, validators=[RegexValidator(r'^\d{8}$', 'Use 8 digitos, sem hifen.')]
    )
    price = models.DecimalField('preco', max_digits=10, decimal_places=2)
    days_min = models.PositiveIntegerField('prazo minimo (dias)')
    days_max = models.PositiveIntegerField('prazo maximo (dias)')
    active = models.BooleanField('ativo', default=True)

    objects = ShippingZoneQuerySet.as_manager()

    def clean(self):
        super().clean()
        if self.cep_start and self.cep_end and self.cep_start > self.cep_end:
            raise ValidationError('O CEP inicial precisa ser menor ou igual ao CEP final.')
        if self.days_min and self.days_max and self.days_min > self.days_max:
            raise ValidationError('O prazo minimo precisa ser menor ou igual ao prazo maximo.')

    class Meta:
        ordering = ['cep_start']
        verbose_name = 'Zona de frete'
        verbose_name_plural = 'Zonas de frete'

    def __str__(self):
        return f'{self.name} (R$ {self.price})'
