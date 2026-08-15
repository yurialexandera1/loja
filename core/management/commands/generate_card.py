"""Gera imagem de produto (modo site ou social) a partir de uma foto crua.

Uso:
  python manage.py generate_card <slug-do-produto> <caminho-da-foto> --mode site
  python manage.py generate_card <slug-do-produto> <caminho-da-foto> --mode social

Salva o resultado como nova ProductImage do produto (nao mexe nas imagens
existentes). Usa nome/preco/pix_price reais do Product ja cadastrado.
"""
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from core.card_generator import generate_site_card, generate_social_card, to_jpeg_bytes
from core.models import Product, ProductImage


class Command(BaseCommand):
    help = 'Gera imagem de produto (site ou social) a partir de foto crua + dados reais do banco.'

    def add_arguments(self, parser):
        parser.add_argument('slug', type=str)
        parser.add_argument('photo_path', type=str)
        parser.add_argument('--mode', choices=['site', 'social'], default='site')

    def handle(self, *args, **options):
        slug = options['slug']
        photo_path = options['photo_path']
        mode = options['mode']

        try:
            product = Product.objects.get(slug=slug)
        except Product.DoesNotExist:
            raise CommandError(f'Produto "{slug}" nao encontrado.')

        try:
            photo = Image.open(photo_path)
        except Exception as exc:
            raise CommandError(f'Nao consegui abrir a foto: {exc}')

        logo = Image.open('static/store/img/logo.png')

        if mode == 'site':
            result = generate_site_card(photo, logo)
        else:
            result = generate_social_card(
                photo, logo, product.name, str(product.price), str(product.pix_price)
            )

        data = to_jpeg_bytes(result)
        image = ProductImage(product=product, order=product.images.count())
        image.image.save(f'{slug}_{mode}.jpg', ContentFile(data), save=True)
        self.stdout.write(self.style.SUCCESS(f'Gerado: {image.image.url}'))
