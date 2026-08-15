"""Importa o catalogo real da Case See (107 produtos), extraido da vitrine
publica em 2026-08-14. Categoria inferida por palavra-chave no nome —
produtos marcados como incertos (categoria 'Acessórios') devem ser
revisados no painel apos a importacao.

Uso: python manage.py import_casesee [--dry-run]
"""

import re
import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Brand, Category, Product

CATEGORIES = [
    ('Acessório Gamer', 'acessorio-gamer', 'package'),
    ('Acessórios', 'acessorios', 'tag'),
    ('Adaptador', 'adaptador', 'zap'),
    ('Alça', 'alca', 'package'),
    ('Bolsas e Mochilas', 'bolsas-mochilas', 'package'),
    ('Brinquedos Eletrônicos', 'brinquedos-eletronicos', 'package'),
    ('Cabos', 'cabos', 'cable'),
    ('Caixa de Som', 'caixa-de-som', 'package'),
    ('Câmera', 'camera', 'package'),
    ('Canetas em Geral', 'canetas', 'package'),
    ('Capa de Tablet', 'capa-de-tablet', 'smartphone'),
    ('Capa de Tablet Infantil', 'capa-de-tablet-infantil', 'smartphone'),
    ('Carregador', 'carregador', 'zap'),
    ('Carregador de Indução', 'carregador-de-inducao', 'battery-charging'),
    ('Controle', 'controle', 'package'),
    ('Cordas', 'cordas', 'package'),
    ('Eletrônicos', 'eletronicos', 'package'),
    ('Fone', 'fone', 'headphones'),
    ('Fontes', 'fontes', 'zap'),
    ('Game', 'game', 'package'),
    ('Houverboard', 'houverboard', 'car'),
    ('Iluminação', 'iluminacao', 'package'),
    ('Massageador', 'massageador', 'package'),
    ('Microfone Bluetooth', 'microfone-bluetooth', 'package'),
    ('Mouse', 'mouse', 'package'),
    ('Produtos Inclusivos', 'produtos-inclusivos', 'tag'),
    ('Pulseiras Smartwatch', 'pulseiras-smartwatch', 'package'),
    ('Smartwatch', 'smartwatch', 'package'),
    ('Suporte', 'suporte', 'package'),
    ('Suporte Veicular', 'suporte-veicular', 'car'),
    ('Teclado', 'teclado', 'package'),
]

# (regex sobre o nome em maiusculas, slug da categoria) — testado em ordem,
# primeiro que casar vence.
KEYWORD_RULES = [
    (r'CORD[AÃ]O DE IDENTIFICA|PULSEIRA DE IDENTIFICA|ABAFADOR|LA[ÇC]O INFANTIL|TIARA|CHAP[ÉE]U INFANTIL', 'produtos-inclusivos'),
    (r'^CABO ', 'cabos'),
    (r'^ALÇA|^ALCA', 'alca'),
    (r'^FONTE ', 'fontes'),
    (r'^FONE |^FONE$', 'fone'),
    (r'CARREGADOR SEM FIO|CARREGADOR.*INDU[ÇC][ÃA]O', 'carregador-de-inducao'),
    (r'CARREGADOR|POWER BANK', 'carregador'),
    (r'^ADAPTADOR', 'adaptador'),
    (r'CAIXA DE SOM', 'caixa-de-som'),
    (r'^C[ÂA]MERA|ESTUDIO FOTOGRAFICO|ESTÚDIO FOTOGRAFICO', 'camera'),
    (r'CAPA TABLET.*INFANTIL', 'capa-de-tablet-infantil'),
    (r'CAPA TABLET|CAPA GAMER', 'capa-de-tablet'),
    (r'CONTROLE|DOUBLESHOCK|DOUBLE MOTOR', 'controle'),
    (r'^CORDA ', 'cordas'),
    (r'MICROFONE', 'microfone-bluetooth'),
    (r'MOUSE', 'mouse'),
    (r'PULSEIRA.*APPLE WATCH|PULSEIRA SPORT|PULSEIRA SILICONE|PULSEIRA IN[ÓO]X|PULSEIRA DE COURO|PULSEIRA ONDULADA|PULSEIRA DE [ÍI]M[ÃA]|KIT CASE E PULSEIRA', 'pulseiras-smartwatch'),
    (r'SMARTWATCH', 'smartwatch'),
    (r'SUPORTE VEICULAR|SUPORTE MOTO|^SMART CAR', 'suporte-veicular'),
    (r'SUPORTE', 'suporte'),
    (r'TECLADO|PIANO FLEX[ÍI]VEL', 'teclado'),
    (r'HOVERKART|HOUVERBOARD', 'houverboard'),
    (r'MASSAGEADOR', 'massageador'),
    (r'BOLSA[- ]', 'bolsas-mochilas'),
    (r'BATERIA ELETR[ÔO]NICA|GAMESTICK|HEADSET GAMER|PS1 |RASTREADOR', 'brinquedos-eletronicos'),
    (r'LÁPIS DIGITAL|HUB USB', 'acessorios'),
]

# nome, codigo, marca (ou None), preco
RAW_PRODUCTS = [
    ('2 CONTROLES MAY-004', '20233', None, '300.00'),
    ('ABAFADOR DE RUÍDO LEF-1219', '1002350', 'LEHMOX', '199.00'),
    ('ABAFADOR SIMPLES', '000042-WP', None, '29.90'),
    ('ACESSÓRIO- DEZENA', '000044-WP', None, '55.00'),
    ('ACESSÓRIO- POP SOCKET GLITTER', '1002352', None, '25.00'),
    ('ACESSÓRIO- POP SOCKET SIMPLES', '1002353', None, '25.00'),
    ('ADAPTADOR 2 EM 1 LIGHTNING P/ TIPO C ADAPT40', '1001964', 'DRIFTIN', '50.00'),
    ('ALÇA BASIC PEQUENA', '000052-WP', None, '45.00'),
    ('ALÇA CAROLINA', '000036-WP', None, '65.00'),
    ('ALÇA DE COURO GRANDE', '000038-WP', None, '99.00'),
    ('ALÇA DE MÃO STAR', '000039-WP', None, '55.00'),
    ('ALÇA RAFAELA', '000037-WP', None, '59.00'),
    ('APOIO DE MÃO PARA CELULAR', '000054-WP', None, '45.00'),
    ('BATERIA ELETRÔNICA ROLL UP 9+1 PADS', '1002349', 'TOMATE', '350.00'),
    ('BOLSA- GARRAFA CELULAR GRANDE', '1002343', None, '100.00'),
    ('BOLSA- GARRAFA CELULAR PEQUENA', '1002342', None, '85.00'),
    ('CABO 1P2 PD30W + CC60W TURBO CB118', '000007-WP', 'AGOLD', '150.00'),
    ('CABO 2EM1 TIPO-C 65W + LIGHTNING 30W CB-34', '1002023', 'AGOLD', '150.00'),
    ('CABO DE ÁUDIO 3.5MM CB-99', '000008-WP', 'AGOLD', '45.00'),
    ('CABO LIGHTNING 5A CB-71', '1002291', 'AGOLD', '65.00'),
    ('CABO TIPO-C 5A CB-70', '1002294', 'AGOLD', '65.00'),
    ('CABO TIPO-C CB101', '1234000020-WP', 'AGOLD', '75.00'),
    ('CABO TIPO-C TC-111CC', '1002339', None, '65.00'),
    ('CABO TURBO TIPO-C CB-105', '1002347', 'AGOLD', '99.00'),
    ('CAIXA DE SOM SM-10', '000009-WP', 'AGOLD', '350.00'),
    ('CAIXA DE SOM SM-31', '1002267', 'AGOLD', '350.00'),
    ('CÂMERA DIGITAL INSTANTÂNEA POLAROID INFANTIL COM IMPRESSÕES', '000032-WP', None, '299.00'),
    ('CAPA GAMER NINTENDO SWTICH NX', '1002000', None, '120.00'),
    ('CAPA TABLET - ADULTO', '1000165', None, '100.00'),
    ('CAPA TABLET- INFANTIL BRACINHO PEQUENA', '1000163', None, '120.00'),
    ('CARREGADOR SEM FIO 3 EM 1 MAGNÉTICO BTE-25', '1002305', 'AGOLD', '100.00'),
    ('CARREGADOR VEÍCULAR DUO CHARGE 4X', '1000737', 'EASY MOBILE', '180.00'),
    ('CARREGADOR VEICULAR SIMPLES FCA-V242', '1000988', 'FAM', '50.00'),
    ('CHAPÉU INFANTIL- ESTAMPA AUTISMO', '1002042', None, '45.00'),
    ('CONTROLE UNIVERSAL X-360 / PS3 / PC / ANDROID', '1002337', None, '250.00'),
    ('CORDA AMALIA', '000019-WP', None, '99.00'),
    ('CORDA MIRELA', '000018-WP', None, '65.00'),
    ('CORDÃO DE IDENTIFICAÇÃO - ESCLEROSE MÚLTIPLA', '000057-WP', None, '25.00'),
    ('CORDÃO DE IDENTIFICAÇÃO - FIBROMIALGIA', '1002373', None, '25.00'),
    ('CORDÃO DE IDENTIFICAÇÃO - GIRASSOL', '1002372', None, '25.00'),
    ('CORDÃO DE IDENTIFICAÇÃO - PARALISIA', '000056-WP', None, '25.00'),
    ('CORDÃO DE IDENTIFICAÇÃO - TDAH', '000058-WP', None, '25.00'),
    ('DOUBLE MOTOR VIBRATION 4 -CONTROLE PS4', '1001994', None, '250.00'),
    ('DOUBLESHOCK P III - CONTROLE PS3', '1002263', None, '200.00'),
    ('FONE BLUETOOTH INFANTIL ELETROMEX EL-1504', '1001985', 'ELETRO MEX', '180.00'),
    ('FONE COM FIO LIGHTNING FN-A58', '1002285', 'AGOLD', '75.00'),
    ('FONE COM FIO TIPO C FN-A77L', '1002286', None, '75.00'),
    ('FONE DE OUVIDO SEM FIO FN-BT8', '000005-WP', 'AGOLD', '300.00'),
    ('FONE DE OUVIDO SEM FIO TWS BLUETOOTH 5.4 FN-BJ3', '000030-WP', 'AGOLD', '199.00'),
    ('FONE INFANTIL XC-HS17', '1002271', None, '120.00'),
    ('Fone Ouvido S/ Fio Bluetooth C/ Microfone Princesas Disney Cor Roxo Luz Enrolados', '000004-WP', None, '150.00'),
    ('FONTE RÁPIDO 2 USB CA16-4', '000026-WP', 'AGOLD', '55.00'),
    ('FONTE TURBO USB-C 40W CA42-4', '000025-WP', 'AGOLD', '99.00'),
    ('FONTE VEICULAR GOLD 2 USB CJ10-4', '1002024', 'AGOLD', '50.00'),
    ('FONTE VEICULAR GOLD CJ05-4', '1002300', 'AGOLD', '50.00'),
    ('GAMESTICK M15 PLUS', '1002264', None, '600.00'),
    ('HEADSET GAMER EJ-904-M', '1002005', None, '250.00'),
    ('HEADSET GAMER KP-GA04', '1002055', None, '250.00'),
    ('HOVERKART', '1000842', None, '750.00'),
    ('HUB USB 3.0 HUB 5 EM 1 CBA-28', '1001963', 'AGOLD', '100.00'),
    ('KIT CARREGADOR iOS CA31-6', '1002299', None, '99.00'),
    ('KIT CARREGADOR RÁPIDO 4.1A LIGHTNING CA16-2/IOS', '000024-WP', 'AGOLD', '85.90'),
    ('KIT CARREGADOR RÁPIDO 4.1A USB-A + CABO USB-C CA22-3', '000023-WP', 'AGOLD', '85.90'),
    ('KIT CARREGADOR TURBO 40W USB-A + USB-C PD 3.0 QC4.0 CA42-2/IOS', '000021-WP', 'AGOLD', '119.90'),
    ('KIT CARREGADOR TURBO 40W USB-A + USB-C PD CA42-5', '000022-WP', 'AGOLD', '119.90'),
    ('KIT CASE E PULSEIRA ESPORTIVA', '000015-WP', None, '99.00'),
    ('LAÇO INFANTIL - ESTAMPA AUTISMO', '1002043', None, '45.00'),
    ('LAÇO INFANTIL- ESTAMPA AUTISMO', '1002340', None, '35.00'),
    ('LÁPIS DIGITAL PARA IPAD E IPAD PRO GN-RD02', '1002336', 'GENAI', '99.00'),
    ('MASSAGEADOR MULTIFUNCIONAL AM-026', '1002338', None, '350.00'),
    ('MICROFONE COM FIO TOMATE MT 1010', '1001974', None, '50.00'),
    ('MICROFONE DE LAPELA GOLD 2 EM 1 LIGHTNING MCF-10', '1001958', 'AGOLD', '300.00'),
    ('MICROFONE DE LAPELA TOMATE 2 EM 1 MT-2216', '1001966', None, '250.00'),
    ('MICROFONE DUPLO LAPELA GOLD MCF-38D', '1002310', 'AGOLD', '350.00'),
    ('MINI ESTÚDIO FOTOGRAFICO B-MAX BM F1131', '1002059', None, '150.00'),
    ('MINI TECLADO USB JP-08 VERDE', '000361', None, '100.00'),
    ('MOUSE GAMER JIEXIN T8', '000365', None, '85.00'),
    ('MOUSE GAMER JIEXIN X14', '000017-WP', None, '100.00'),
    ('PIANO FLEXÍVEL 49 TECLAS', '000031-WP', 'TOMATE', '250.00'),
    ('PINGENTES', '1002375', None, '35.00'),
    ('POP SOCKET INDUÇÃO COM BRILHO', '000034-WP', None, '85.00'),
    ('POP SOCKET SILICONADO', '000035-WP', None, '85.00'),
    ('PORTA CARTÃO', '000061-WP', None, '25.00'),
    ('POWER BANK MAGNÉTICO AGOLD BTE-60B', '000027-WP', 'AGOLD', '299.00'),
    ('PS1 MAY-032', '1002261', None, '450.00'),
    ('PULSEIRA DE COURO', '000048-WP', None, '99.00'),
    ('PULSEIRA DE IDENTIFICAÇÃO - AUTISMO', '000055-WP', None, '20.00'),
    ('PULSEIRA DE IDENTIFICAÇÃO - GIRASSOL', '1000825', None, '20.00'),
    ('PULSEIRA DE ÍMÃ EXECUTIVO', '000046-WP', None, '99.00'),
    ('PULSEIRA INOX', '000045-WP', None, '150.00'),
    ('PULSEIRA MILANESE LOOP MAGNÉTICA PARA APPLE WATCH ROSE GOLD', '000014-WP', None, '80.00'),
    ('PULSEIRA ONDULADA', '000047-WP', None, '60.00'),
    ('PULSEIRA SILICONE', '1002346', None, '45.00'),
    ('PULSEIRA SPORT', '000016-WP', None, '60.00'),
    ('RASTREADOR DE DISPOSITIVO TCD-06', '1002335', 'AGOLD', '99.00'),
    ('SMART CAR 6.0', '1000893', 'EASY MOBILE', '150.00'),
    ('SMARTWATCH GOLD RL-10', '1002279', 'AGOLD', '350.00'),
    ('Suporte Headphone / Headset', '000011-WP', None, '85.00'),
    ('SUPORTE MOTO A PROVA DAGUA TOMATE MTG-016M', '1001960', None, '100.00'),
    ('SUPORTE PARA TABLET TOMATE MTG 037', '1002035', None, '150.00'),
    ('SUPORTE VEICULAR COM VENTOSA MTG-206', '000028-WP', 'TOMATE', '75.00'),
    ('TECLADO GAMER XTRAD HK8400', '1002004', None, '250.00'),
    ('TECLADO LEHMOX LEY 2075', '1002265', None, '180.00'),
    ('TERÇO DE MÃO', '000043-WP', None, '99.00'),
    ('TIARA - ESTAMPA AUTISMO', '1002341', None, '45.00'),
    ('VENTOSA GRANDE', '1002378', None, '25.00'),
    ('VENTOSA PEQUENA', '1002380', None, '15.00'),
]


def _slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


def _guess_category_slug(name):
    upper = name.upper()
    for pattern, slug in KEYWORD_RULES:
        if re.search(pattern, upper):
            return slug
    return None


class Command(BaseCommand):
    help = 'Importa os 107 produtos reais da Case See a partir da lista fixa embutida.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Mostra o que seria feito sem gravar nada no banco.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        with transaction.atomic():
            categories = {}
            for order, (name, slug, icon) in enumerate(CATEGORIES):
                cat, _ = Category.objects.get_or_create(
                    slug=slug, defaults={'name': name, 'icon': icon, 'order': order}
                )
                categories[slug] = cat

            brands = {}
            created, updated, uncertain = 0, 0, []

            for name, sku, brand_name, price in RAW_PRODUCTS:
                brand = None
                if brand_name:
                    if brand_name not in brands:
                        brands[brand_name] = Brand.objects.get_or_create(
                            slug=_slugify(brand_name), defaults={'name': brand_name}
                        )[0]
                    brand = brands[brand_name]

                cat_slug = _guess_category_slug(name)
                if cat_slug is None:
                    uncertain.append((name, sku))
                    category = categories['acessorios']
                else:
                    category = categories[cat_slug]

                sku_slug = _slugify(sku)
                name_slug = _slugify(name)[: 49 - len(sku_slug)]
                product_slug = f'{name_slug}-{sku_slug}'.strip('-')[:50]
                defaults = {
                    'name': name.strip(),
                    'slug': product_slug,
                    'brand': brand,
                    'category': category,
                    'price': price,
                    'stock': 5,
                    'active': True,
                }
                obj, was_created = Product.objects.update_or_create(sku=sku, defaults=defaults)
                if was_created:
                    created += 1
                else:
                    updated += 1

            self.stdout.write(f'Categorias: {len(categories)}')
            self.stdout.write(f'Marcas: {len(brands)}')
            self.stdout.write(f'Produtos criados: {created} | atualizados: {updated}')
            if uncertain:
                self.stdout.write(self.style.WARNING(
                    f'\n{len(uncertain)} produto(s) com categoria incerta '
                    f'(caíram em "Acessórios", revise no painel):'
                ))
                for name, sku in uncertain:
                    self.stdout.write(f'  - {name} (cód. {sku})')

            if dry_run:
                self.stdout.write(self.style.WARNING('\n--dry-run: desfazendo tudo.'))
                transaction.set_rollback(True)
