from core.models import BlogPost, Brand, Category, Coupon, ShippingZone
from panel.crud import crud_views

categorias_list, categoria_nova, categoria_editar, categoria_remover = crud_views(
    model=Category,
    form_fields=['name', 'slug', 'icon', 'order', 'seo_text'],
    columns=[('name', 'Nome'), ('slug', 'Slug'), ('order', 'Ordem')],
    name_singular='categoria',
    name_plural='Categorias',
    slug='categorias',
    list_url_name='panel:categorias',
    create_url_name='panel:categoria_nova',
    edit_url_name='panel:categoria_editar',
    delete_url_name='panel:categoria_remover',
)

marcas_list, marca_nova, marca_editar, marca_remover = crud_views(
    model=Brand,
    form_fields=['name', 'slug'],
    columns=[('name', 'Nome'), ('slug', 'Slug')],
    name_singular='marca',
    name_plural='Marcas',
    slug='marcas',
    list_url_name='panel:marcas',
    create_url_name='panel:marca_nova',
    edit_url_name='panel:marca_editar',
    delete_url_name='panel:marca_remover',
)

cupons_list, cupom_novo, cupom_editar, cupom_remover = crud_views(
    model=Coupon,
    form_fields=['code', 'percent_off', 'active', 'expires_at', 'max_uses'],
    columns=[
        ('code', 'Código'), ('percent_off', 'Desconto (%)'),
        ('used_count', 'Usos'), ('active', 'Ativo'),
    ],
    name_singular='cupom',
    name_plural='Cupons',
    slug='cupons',
    list_url_name='panel:cupons',
    create_url_name='panel:cupom_novo',
    edit_url_name='panel:cupom_editar',
    delete_url_name='panel:cupom_remover',
)

fretes_list, frete_novo, frete_editar, frete_remover = crud_views(
    model=ShippingZone,
    form_fields=['name', 'cep_start', 'cep_end', 'price', 'days_min', 'days_max', 'active'],
    columns=[
        ('name', 'Zona'), ('cep_start', 'CEP inicial'), ('cep_end', 'CEP final'),
        ('price', 'Preço'), ('active', 'Ativa'),
    ],
    name_singular='zona de frete',
    name_plural='Zonas de frete',
    slug='fretes',
    list_url_name='panel:fretes',
    create_url_name='panel:frete_novo',
    edit_url_name='panel:frete_editar',
    delete_url_name='panel:frete_remover',
)

posts_list, post_novo, post_editar, post_remover = crud_views(
    model=BlogPost,
    form_fields=['title', 'slug', 'excerpt', 'body', 'cover_icon', 'published'],
    columns=[('title', 'Título'), ('published', 'Publicado'), ('created_at', 'Criado em')],
    name_singular='artigo',
    name_plural='Blog',
    slug='posts',
    list_url_name='panel:posts',
    create_url_name='panel:post_novo',
    edit_url_name='panel:post_editar',
    delete_url_name='panel:post_remover',
)
