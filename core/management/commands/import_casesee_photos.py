"""Anexa as fotos reais da Case See aos produtos ja importados por
import_casesee. As fotos foram baixadas de /casesee/category/<slug> na
vitrine publica (mesmas imagens que qualquer visitante ve no navegador) e
ficam staged em <BASE_DIR>/var/casesee_photos_staging/<sku>.jpg antes de
rodar este comando (diretorio dedicado do projeto, nao /tmp compartilhado,
para evitar symlink attack/race condition de outros usuarios do host).

Redimensiona para no maximo 1000px no lado maior e recomprime em JPEG
qualidade 82 — os arquivos originais chegam a 1MB+ cada, pesados demais
pra servir direto numa vitrine com 100+ produtos.

Uso: python manage.py import_casesee_photos [--dry-run]
"""

import io
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, UnidentifiedImageError

from core.models import Product, ProductImage

STAGING_DIR = str(settings.BASE_DIR / 'var' / 'casesee_photos_staging')
MAX_DIMENSION = 1000
JPEG_QUALITY = 82


class Command(BaseCommand):
    help = 'Anexa as fotos reais baixadas da vitrine Nex aos produtos correspondentes.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        os.makedirs(STAGING_DIR, mode=0o700, exist_ok=True)
        os.chmod(STAGING_DIR, 0o700)

        try:
            staged_files = os.listdir(STAGING_DIR)
        except (PermissionError, OSError) as exc:
            self.stderr.write(self.style.ERROR(
                f'Nao foi possivel ler a pasta {STAGING_DIR}: {exc}'
            ))
            return

        if not staged_files:
            self.stderr.write(self.style.ERROR(
                f'Pasta {STAGING_DIR} esta vazia. Copie as fotos baixadas '
                'para la antes de rodar este comando.'
            ))
            return

        attached, skipped_existing, not_found, failed = 0, 0, [], []
        dry_run = options['dry_run']

        # A escrita do arquivo em disco (FileField.save) nao participa da
        # transacao de banco — um rollback desfaz a linha, mas nao o arquivo.
        # Por isso, em --dry-run nunca chamamos ProductImage.objects.create();
        # so contamos o que seria feito.
        with transaction.atomic():
            for filename in sorted(staged_files):
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                sku = os.path.splitext(filename)[0]
                product = Product.objects.filter(sku=sku).first()
                if product is None:
                    not_found.append(sku)
                    continue
                if product.images.exists():
                    skipped_existing += 1
                    continue

                if not dry_run:
                    path = os.path.join(STAGING_DIR, filename)
                    try:
                        content = self._resize(path)
                    except (UnidentifiedImageError, OSError) as exc:
                        self.stdout.write(self.style.ERROR(
                            f'Falha ao processar imagem {filename}: {exc}'
                        ))
                        failed.append(filename)
                        continue
                    ProductImage.objects.create(
                        product=product,
                        image=ContentFile(content, name=f'{sku}.jpg'),
                        alt=product.name,
                        order=0,
                    )
                attached += 1

            self.stdout.write(f'Fotos anexadas: {attached}')
            self.stdout.write(f'Produtos que ja tinham foto (pulados): {skipped_existing}')
            if not_found:
                self.stdout.write(self.style.WARNING(
                    f'{len(not_found)} arquivo(s) sem produto correspondente: {not_found}'
                ))
            if failed:
                self.stdout.write(self.style.WARNING(
                    f'{len(failed)} arquivo(s) com falha no processamento: {failed}'
                ))

            if dry_run:
                self.stdout.write(self.style.WARNING('--dry-run: nenhum arquivo foi gravado.'))
                transaction.set_rollback(True)

    def _resize(self, path):
        with Image.open(path) as img:
            img = img.convert('RGB')
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=True)
            return buffer.getvalue()
