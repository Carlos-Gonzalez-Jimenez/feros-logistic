import os

import pandas as pd
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from blog.models import Tag, BlogCategory, Post
from cms.models import (
    Landing,
    Blocks,
    Header,
    Footer,
    ShopPage,
    BlogPage,
    BlockNAVBAR,
)
from core.models import (
    Currency,
    Measurement_Unit,
    Product,
    Brand,
    Provider,
    Country,
    Category,
    OrderStatus,
    Province,
    Municipality,
    NotificationType,
    Specifications,
    Config,
)
from delivery.models import ShippingZone, ShippingMethod, ShippingRate
from f_backend.settings import APPLICATION_DATA_PATH
from payments.models import PaymentMethod, Wallet
from user.models import User

# python manage.py seed


class Command(BaseCommand):
    """script to seed database

    Args:
        BaseCommand (_type_): _description_
    """

    help = "seed database for testing and development."

    def add_arguments(self, parser):
        parser.add_argument("--mode", type=str, help="Mode")

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("seeding data..."))
        self.run_seed()
        self.stdout.write(self.style.WARNING("done."))

    def create_cms_infrastructure(self) -> None:
        """Creates cms infrastructure objects"""

        self.stdout.write(self.style.NOTICE("start populating cms infrastructure"))

        if not Landing.objects.first():
            Landing.objects.create()
        if not Header.objects.first():
            navbar = BlockNAVBAR.objects.first() or BlockNAVBAR.objects.create(
                label="Menú principal", items=[{"label": "Productos", "to": "/shop"}]
            )
            Header.objects.create(out_menu=navbar, in_menu=navbar)
        if not Footer.objects.first():
            Footer.objects.create(design="1/4")
        if not ShopPage.objects.first():
            ShopPage.objects.create(title="Tienda", design="1", orientation="1/4")
        if not BlogPage.objects.first():
            BlogPage.objects.create(title="Tienda", design="1", orientation="1/4")

        # Content Types
        page_content_type = ContentType.objects.get(model="page")
        block_html_content_type = ContentType.objects.get(model="blockhtml")
        block_button_content_type = ContentType.objects.get(model="blockbutton")
        block_media_content_type = ContentType.objects.get(model="blockmedia")
        block_card_group_content_type = ContentType.objects.get(model="blockcardgroup")
        block_card_content_type = ContentType.objects.get(model="blockcard")
        block_product_content_type = ContentType.objects.get(model="product")
        block_category_content_type = ContentType.objects.get(model="category")
        block_brand_content_type = ContentType.objects.get(model="brand")
        block_carousel_content_type = ContentType.objects.get(model="blockcarousel")
        block_hero_content_type = ContentType.objects.get(model="blockhero")
        block_cta_content_type = ContentType.objects.get(model="blockcta")
        block_footer_content_type = ContentType.objects.get(model="footer")
        block_footer_links_content_type = ContentType.objects.get(
            model="blockfooterlinks"
        )
        # block_header_content_type = ContentType.objects.get(model="header")
        # block_navbar_content_type = ContentType.objects.get(model="blocknavbar")
        block_landing_content_type = ContentType.objects.get(model="landing")
        block_post_content_type = ContentType.objects.get(model="post")
        block_media_card_content_type = ContentType.objects.get(model="blockmediacard")
        block_container_content_type = ContentType.objects.get(model="blockcontainer")
        block_marquee_content_type = ContentType.objects.get(model="blockmarquee")
        block_shop_page_content_type = ContentType.objects.get(model="shoppage")
        block_blog_page_content_type = ContentType.objects.get(model="blogpage")
        block_filter_product_content_type = ContentType.objects.get(
            model="blockfilterproduct"
        )
        block_filter_post_content_type = ContentType.objects.get(
            model="blockfilterpost"
        )
        block_filter_brand_content_type = ContentType.objects.get(
            model="blockfilterbrand"
        )
        # Blocks

        _ = Blocks.objects.create(
            name="Filter Product",
            label="{{label}}",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_filter_product_content_type,
        )

        _ = Blocks.objects.create(
            name="Filter Post",
            label="{{label}}",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_filter_post_content_type,
        )
        _ = Blocks.objects.create(
            name="Filter Brand",
            label="{{label}}",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_filter_brand_content_type,
        )
        _ = Blocks.objects.create(
            name="Container",
            label="{{label}}",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_container_content_type,
        )

        _ = Blocks.objects.create(
            name="Marquee",
            label="{{label}}",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_marquee_content_type,
        )

        _ = Blocks.objects.create(
            name="Landing Page",
            label="block landing page",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_landing_content_type,
        )

        _ = Blocks.objects.create(
            name="Post",
            label="{{title}}",
            color="info",
            icon="mdi:post-outline",
            content_type=block_post_content_type,
        )

        _ = Blocks.objects.create(
            name="Shop Page",
            label="{{title}}",
            color="info",
            icon="line-md:confirm-square-to-square-transition",
            content_type=block_shop_page_content_type,
        )

        _ = Blocks.objects.create(
            name="Blog Page",
            label="{{title}}",
            color="info",
            icon="ic:outline-post-add",
            content_type=block_blog_page_content_type,
        )

        _ = Blocks.objects.create(
            name="Media Card",
            label="{{label}}",
            color="info",
            icon="mdi:card-account-details-star-outline",
            content_type=block_media_card_content_type,
        )

        _ = Blocks.objects.create(
            name="Footer Links",
            label="{{title}}",
            color="info",
            icon="mdi:list-box",
            content_type=block_footer_links_content_type,
        )

        _ = Blocks.objects.create(
            name="Hero",
            label="{{label}}",
            color="info",
            icon="mdi:file-table-box-multiple",
            content_type=block_hero_content_type,
        )

        _ = Blocks.objects.create(
            name="CTA",
            label="{{title}}",
            color="info",
            icon="mdi:file-table-box-multiple",
            content_type=block_cta_content_type,
        )

        _ = Blocks.objects.create(
            name="Carousel",
            label="{{name}}",
            color="info",
            icon="mdi-view-carousel",
            content_type=block_carousel_content_type,
        )

        _ = Blocks.objects.create(
            name="Producto",
            label="{{name}}",
            color="info",
            icon="mdi-package-variant",
            content_type=block_product_content_type,
        )

        _ = Blocks.objects.create(
            name="Categoría",
            label="{{name}}",
            color="info",
            icon="mdi-tag-multiple",
            content_type=block_category_content_type,
        )

        _ = Blocks.objects.create(
            name="Marca",
            label="{{name}}",
            color="info",
            icon="mdi-tag-multiple",
            content_type=block_brand_content_type,
        )

        _ = Blocks.objects.create(
            name="Html",
            label="{{label}}",
            color="info",
            icon="mdi-language-html5",
            content_type=block_html_content_type,
        )

        _ = Blocks.objects.create(
            name="Boton",
            label="block button",
            color="info",
            icon="mdi-button-pointer",
            content_type=block_button_content_type,
        )

        _ = Blocks.objects.create(
            name="Media",
            label="{{name}} {{size}}",
            color="info",
            icon="mdi-file-image",
            content_type=block_media_content_type,
        )

        _ = Blocks.objects.create(
            name="Grupo de tarjetas",
            label="{{label}}",
            color="info",
            icon="mdi-view-dashboard",
            content_type=block_card_group_content_type,
        )

        _ = Blocks.objects.create(
            name="Tarjeta",
            label="{{label}} {{title}}",
            color="info",
            icon="mdi-card-text-outline",
            content_type=block_card_content_type,
        )

    def create_configuration(self) -> None:
        """Create configuration object"""

        self.stdout.write(self.style.NOTICE("start creating configuration object"))

        config = Config.objects.create(
            business_name="FEROS GRUPO S.U.R.L.",
            business_address="Ave. 41 #12208 e/122 y 124, Marianao, La Habana",
            logo_light="config/logo.png",
            logo_horizontal_light="config/logo_horizontal.png",
            logo_dark="config/logo_negativo.png",
            logo_horizontal_dark="config/logo_horizontal_negativo.png",
            admin_logo_horizontal_light="config/admin_logo_horizontal.png",
            admin_logo_horizontal_dark="config/admin_logo_horizontal_negativo.png",
            front_url="https://localhost:3000",
            recover_password_url="https://localhost:3000/forgot-password",
            confirm_register_url="https://localhost:3000/confirm-register",
            login_url="https://localhost:3000/login",
            ecommerce_commission_is_percentage=True,
            ecommerce_commission_value=4.5,
            waha_api_url="https://whatsapp.pavelcode5426.duckdns.org",
            waha_api_user="pavelcode5426",
            waha_api_password="pavelcode5426",
            enzona_api_url="https://api.enzona.net",
            enzona_consumer_key="",
            enzona_consumer_secret="",
            transfermovil_api_url="http://152.206.64.213:15000",
            transfermovil_username="",
            transfermovil_seed="",
            transfermovil_source="",
            tropipay_api_url="https://sandbox.tropipay.me",
            tropipay_client_id="",
            tropipay_client_secret="",
            astrack_url="https://astrackcuba.alascloud.com",
            astrack_websocket="wss://astrackcuba.alascloud.com"
        )

    def create_currencies(self) -> None:
        """Creates all currencies objects"""

        self.stdout.write(self.style.NOTICE("start populating currencies"))

        currencies = [
            ("Dólar USA", "USD", "$", 0.0022, True),
            ("Euro", "EUR", "€", 0.001, False),
            ("Peso Cubano", "CUP", "$", 1.00, False),
        ]

        for currency in currencies:
            _ = Currency.objects.get_or_create(
                name=currency[0],
                initials=currency[1],
                symbol=currency[2],
                exchange_rate=currency[3],
                default=currency[4],
            )

    def create_post(self) -> None:
        """Creates example post objects"""

        self.stdout.write(self.style.NOTICE("start populating post"))

        posts = [
            (
                "¡Lorem ipsum! 🌟",
                "aaaaaaaaaaaaaa bbbbbbbbbbbbbb ccccccccccccc ddddddddddddddd eeeeeeeeeeeeeeeeeeeeeeee ffffffffffffffffffff",
                "published",
            ),
        ]

        for post in posts:
            _ = Post.objects.get_or_create(
                title=post[0],
                slug=slugify(post[0]),
                summary=post[1],
                status=post[2],
                author_id=1,
                category_id=1,
                published_date=timezone.now(),
            )

    def create_countries(self) -> None:
        """Creates all countries objects"""

        self.stdout.write(self.style.NOTICE("start populating countries"))

        excel = pd.read_excel(
            APPLICATION_DATA_PATH + "paises.xlsx", engine="openpyxl"
        ).fillna("")

        for index, _ in excel.iterrows():
            name = excel.at[index, excel.columns[0]].strip()
            code_alpha3 = excel.at[index, excel.columns[1]].strip().upper()
            file_path = f"media/flags/pics/{code_alpha3}.png"
            if os.path.exists(file_path):
                country_flag = f"flags/pics/{code_alpha3}.png"
            else:
                country_flag = "flags/flag_image_default.png"
            country = Country(
                name=name,
                code_alpha3=code_alpha3,
                country_flag=country_flag,
            )
            country.save()

    def create_order_statuses(self) -> None:
        """Creates all status objects"""

        self.stdout.write(self.style.NOTICE("start populating statuses"))

        statuses = [
            ("Creado", "created", 1, True, False, True, True, "info", "mdi-file-plus"),
            (
                "En preparación",
                "in_preparation",
                2,
                False,
                False,
                True,
                True,
                "warning",
                "mdi-magnify",
            ),
            (
                "Listo para recoger",
                "pick_up",
                3,
                False,
                False,
                True,
                False,
                "warning",
                "mdi-cube-outline",
            ),
            (
                "Listo para envío",
                "ready_shipping",
                4,
                False,
                False,
                False,
                True,
                "warning",
                "mdi-cube",
            ),
            (
                "En camino",
                "on_way",
                5,
                False,
                False,
                False,
                True,
                "primary",
                "mdi-motorbike",
            ),
            (
                "Entregado",
                "delivered",
                6,
                False,
                False,
                True,
                True,
                "primary",
                "mdi-truck-check",
            ),
            (
                "Completado",
                "completed",
                7,
                False,
                True,
                True,
                True,
                "success",
                "mdi-check-circle-outline",
            ),
            (
                "Cancelado",
                "cancelled",
                8,
                False,
                True,
                True,
                True,
                "error",
                "mdi-cancel",
            ),
        ]

        for status in statuses:
            _ = OrderStatus.objects.get_or_create(
                name=status[0],
                code_name=status[1],
                order=status[2],
                initial_status=status[3],
                final_status=status[4],
                store_status=status[5],
                delivery_status=status[6],
                color=status[7],
                icon=status[8],
            )

    def create_payment_methods(self) -> None:
        """Creates all payment methods objects"""

        self.stdout.write(self.style.NOTICE("start populating payment methods"))

        payment_methods = [
            (
                "USD Efectivo",
                "payment_methods/payment_method_default.png",
                "usd_cash",
                "USD",
                True,
                True,
                True,
            ),
            (
                "CUP Efectivo",
                "payment_methods/payment_method_default.png",
                "cup_cash",
                "CUP",
                True,
                True,
                True,
            ),
            (
                "Transfermovil",
                "payment_methods/pics/transfermovil.png",
                "transfermovil",
                "CUP",
                True,
                False,
                False,
            ),
            (
                "EnZona",
                "payment_methods/pics/enzona.png",
                "en_zona",
                "CUP",
                True,
                False,
                False,
            ),
            (
                "Wallet",
                "payment_methods/pics/wallet.png",
                "wallet",
                "USD",
                True,
                False,
                True,
            ),
            (
                "Zelle",
                "payment_methods/pics/zelle.png",
                "zelle",
                "USD",
                False,
                False,
                False,
            ),
            (
                "PayPal",
                "payment_methods/pics/paypal.png",
                "paypal",
                "USD",
                False,
                False,
                False,
            ),
            (
                "Stripe",
                "payment_methods/pics/stripe.png",
                "stripe",
                "USD",
                False,
                False,
                False,
            ),
        ]

        for payment_method in payment_methods:
            currency = Currency.objects.get(initials=payment_method[3])
            _ = PaymentMethod.objects.get_or_create(
                name=payment_method[0],
                logo_payment_method=payment_method[1],
                code_name=payment_method[2],
                currency=currency,
                active=payment_method[4],
                use_in_pos=payment_method[5],
                use_in_store=payment_method[6],
            )

    def create_blog_tags(self) -> None:
        """Creates all tags objects"""

        self.stdout.write(self.style.NOTICE("start populating blog tags"))

        tags = [
            "pollo",
            "productos VIMA",
            "huevos",
            "arroz",
            "atún",
        ]

        for tag in tags:
            _ = Tag.objects.get_or_create(name=tag)

    def create_blog_categories(self) -> None:
        """Creates all blog categories objects"""

        self.stdout.write(self.style.NOTICE("start populating blog categories"))

        categories = ["Pollos", "Huevos", "Arroz", "Atún", "Productos VIMA"]

        for category in categories:
            _ = BlogCategory.objects.get_or_create(name=category)

    def create_shipping_zones(self) -> None:
        """Creates all shipping zones objects"""

        self.stdout.write(self.style.NOTICE("start populating shipping zones"))

        shipping_zones = [
            ("Habana Norte", ["Plaza", "Centro Habana", "Habana Vieja"]),
            ("Habana Sur", ["Diez de Octubre", "Cerro", "Arroyo Naranjo", "Boyeros"]),
            (
                "Habana Este",
                [
                    "Habana del Este",
                    "Guanabacoa",
                    "Regla",
                    "San Miguel del Padrón",
                    "Cotorro",
                ],
            ),
            ("Habana Oeste", ["Playa", "Marianao", "La Lisa"]),
        ]

        for shipping_zone in shipping_zones:
            shipping_zone_obj, _ = ShippingZone.objects.get_or_create(
                name=shipping_zone[0]
            )
            municipalities = shipping_zone[1]
            for municipality in municipalities:
                municipality_obj = Municipality.objects.get(name=municipality)
                shipping_zone_obj.municipalities.add(municipality_obj)

    def create_shipping_methods(self) -> None:
        """Creates all shipping methods objects"""

        self.stdout.write(self.style.NOTICE("start populating shipping methods"))

        shipping_methods = [
            ("Estándar", "standard"),
            ("Express", "express"),
        ]

        for shipping_method in shipping_methods:
            _ = ShippingMethod.objects.get_or_create(
                name=shipping_method[0],
                shipping_method_type=shipping_method[1],
            )

    def create_shipping_rates(self) -> None:
        """Creates all shipping rates objects"""

        self.stdout.write(self.style.NOTICE("start populating shipping rates"))

        shipping_rates = [
            ("Habana Norte", "Estándar", 8.98, 15),
            ("Habana Sur", "Estándar", 7.45, 12),
            ("Habana Este", "Estándar", 10.22, 25),
            ("Habana Oeste", "Estándar", 9.33, 18),
            ("Habana Norte", "Express", 18.98, 10),
            ("Habana Sur", "Express", 17.45, 11),
            ("Habana Este", "Express", 14.22, 15),
            ("Habana Oeste", "Express", 19.33, 12),
        ]

        for shipping_rate in shipping_rates:
            shipping_zone = ShippingZone.objects.get(name=shipping_rate[0])
            shipping_method = ShippingMethod.objects.get(name=shipping_rate[1])
            _ = ShippingRate.objects.get_or_create(
                shipping_zone=shipping_zone,
                shipping_method=shipping_method,
                price=shipping_rate[2],
                estimated_delivery_time=shipping_rate[3],
            )

    def create_specifications(self) -> None:
        """Creates all specifications objects"""

        self.stdout.write(
            self.style.NOTICE("start populating specifications and details")
        )
        specification1, _ = Specifications.objects.get_or_create(
            name="Modo de empleo", icon="mdi:clipboard-text-play-outline"
        )
        specification2, _ = Specifications.objects.get_or_create(
            name="Beneficios", icon="mdi:check-circle-outline"
        )
        specification3, _ = Specifications.objects.get_or_create(
            name="Ingredientes", icon="mdi:format-list-bulleted-type"
        )
        specification4, _ = Specifications.objects.get_or_create(
            name="Formato", icon="mdi-package-variant"
        )
        specification5, _ = Specifications.objects.get_or_create(
            name="Composición", icon="mdi-nutrition"
        )
        specification6, _ = Specifications.objects.get_or_create(
            name="Precauciones", icon="mdi-message-alert"
        )
        # for specification_detail in specification_details:
        #     _ = SpecificationDetails.objects.get_or_create(
        #         name=specification_detail[0],
        #         description=specification_detail[1],
        #         specification=specification,
        #         specification_image=specification_detail[2],
        #     )

    def create_measurement_units(self) -> None:
        """Creates all measurement units objects"""

        self.stdout.write(self.style.NOTICE("start populating measurement units"))

        measurement_units = [
            ("Caja", "CAJ"),
            ("Paca", "PAC"),
            ("Unidad", "UND"),
            ("Pomo", "POM"),
        ]

        for measurement_unit in measurement_units:
            _ = Measurement_Unit.objects.get_or_create(
                name=measurement_unit[0], abbreviation=measurement_unit[1]
            )

    def create_categories(self) -> None:
        """Creates all product's categories objects"""

        self.stdout.write(self.style.NOTICE("start populating product's categories"))

        categories = [
            ("Pollos", None),
            ("Huevos", None),
            ("Arroz", None),
            ("Atún", None),
            ("Productos VIMA", None),
        ]

        for category in categories:
            _ = Category.objects.get_or_create(
                name=category[0],
                parent=(
                    None
                    if category[1] is None
                    else Category.objects.get(name=categories[category[1]][0])
                ),
            )

    def create_providers(self) -> None:
        """Creates all providers objects"""

        self.stdout.write(self.style.NOTICE("start populating providers"))

        providers = ["TYSON", "HOUSE OF RAEFORD", "UNCLE SAM", "ATLANTIKO", "VIMA"]

        for provider in providers:
            _ = Provider.objects.get_or_create(name=provider)

    def create_provinces(self) -> None:
        """Creates all provinces and municipalities objects"""

        self.stdout.write(
            self.style.NOTICE("start populating provinces and municipalities")
        )

        provinces = [
            (
                "Pinar del Río",
                [
                    "Consolación del Sur",
                    "Guane",
                    "La Palma",
                    "Los Palacios",
                    "Mantua",
                    "Minas de Matahambre",
                    "Pinar del Río",
                    "San Juan y Martínez",
                    "San Luis",
                    "Sandino",
                    "Viñales",
                ],
            ),
            (
                "Artemisa",
                [
                    "Alquízar",
                    "Artemisa",
                    "Bauta",
                    "Caimito",
                    "Guanajay",
                    "Güira de Melena",
                    "Mariel",
                    "San Antonio de los Baños",
                    "Bahía Honda",
                    "San Cristóbal",
                    "Candelaria",
                ],
            ),
            (
                "Mayabeque",
                [
                    "Batabanó",
                    "Bejucal",
                    "Güines",
                    "Jaruco",
                    "Madruga",
                    "Melena del Sur",
                    "Nueva Paz",
                    "Quivicán",
                    "San José de las Lajas",
                    "San Nicolás de Bari",
                    "Santa Cruz del Norte",
                ],
            ),
            (
                "La Habana",
                [
                    "Arroyo Naranjo",
                    "Boyeros",
                    "Centro Habana",
                    "Cerro",
                    "Cotorro",
                    "Diez de Octubre",
                    "Guanabacoa",
                    "Habana del Este",
                    "Habana Vieja",
                    "La Lisa",
                    "Marianao",
                    "Playa",
                    "Plaza",
                    "Regla",
                    "San Miguel del Padrón",
                ],
            ),
            (
                "Matanzas",
                [
                    "Calimete",
                    "Cárdenas",
                    "Ciénaga de Zapata",
                    "Colón",
                    "Jagüey Grande",
                    "Jovellanos",
                    "Limonar",
                    "Los Arabos",
                    "Martí",
                    "Matanzas",
                    "Pedro Betancourt",
                    "Perico",
                    "Unión de Reyes",
                ],
            ),
            (
                "Cienfuegos",
                [
                    "Abreus",
                    "Aguada de Pasajeros",
                    "Cienfuegos",
                    "Cruces",
                    "Cumanayagua",
                    "Palmira",
                    "Rodas",
                    "Santa Isabel de las Lajas",
                ],
            ),
            (
                "Villa Clara",
                [
                    "Caibarién",
                    "Camajuaní",
                    "Cifuentes",
                    "Corralillo",
                    "Encrucijada",
                    "Manicaragua",
                    "Placetas",
                    "Quemado de Güines",
                    "Ranchuelo",
                    "Remedios",
                    "Sagua la Grande",
                    "Santa Clara",
                    "Santo Domingo",
                ],
            ),
            (
                "Sancti Spíritus",
                [
                    "Cabaigúan",
                    "Fomento",
                    "Jatibonico",
                    "La Sierpe",
                    "Sancti Spíritus",
                    "Taguasco",
                    "Trinidad",
                    "Yaguajay",
                ],
            ),
            (
                "Ciego de Ávila",
                [
                    "Ciro Redondo",
                    "Baraguá",
                    "Bolivia",
                    "Chambas",
                    "Ciego de Ávila",
                    "Florencia",
                    "Majagua",
                    "Morón",
                    "Primero de Enero",
                    "Venezuela",
                ],
            ),
            (
                "Camagüey",
                [
                    "Camagüey",
                    "Carlos Manuel de Céspedes",
                    "Esmeralda",
                    "Florida",
                    "Guaimaro",
                    "Jimagüayú",
                    "Minas",
                    "Najasa",
                    "Nuevitas",
                    "Santa Cruz del Sur",
                    "Sibanicú",
                    "Sierra de Cubitas",
                    "Vertientes",
                ],
            ),
            (
                "Las Tunas",
                [
                    "Amancio Rodríguez",
                    "Colombia",
                    "Jesús Menéndez",
                    "Jobabo",
                    "Las Tunas",
                    "Majibacoa",
                    "Manatí",
                    "Puerto Padre",
                ],
            ),
            (
                "Holguín",
                [
                    "Antilla",
                    "Báguanos",
                    "Banes",
                    "Cacocum",
                    "Calixto García",
                    "Cueto",
                    "Frank País",
                    "Gibara",
                    "Holguín",
                    "Mayarí",
                    "Moa",
                    "Rafael Freyre",
                    "Sagua de Tánamo",
                    "Urbano Noris",
                ],
            ),
            (
                "Santiago de Cuba",
                [
                    "Contramaestre",
                    "Guamá",
                    "Julio Antonio Mella",
                    "Palma Soriano",
                    "San Luis",
                    "Santiago de Cuba",
                    "Segundo Frente",
                    "Songo la Maya",
                    "Tercer Frente",
                ],
            ),
            (
                "Guantánamo",
                [
                    "Baracoa",
                    "Caimanera",
                    "El Salvador",
                    "Guantánamo",
                    "Imías",
                    "Maisí",
                    "Manuel Tames",
                    "Niceto Pérez",
                    "San Antonio del Sur",
                    "Yateras",
                ],
            ),
            ("Isla de la Juventud", ["Isla de la Juventud"]),
            (
                "Granma",
                [
                    "Bartolomé Masó",
                    "Bayamo",
                    "Buey Arriba",
                    "Campechuela",
                    "Cauto Cristo",
                    "Guisa",
                    "Jiguaní",
                    "Manzanillo",
                    "Media Luna",
                    "Niquero",
                    "Pilón",
                    "Río Cauto",
                    "Yara",
                ],
            ),
        ]

        for province in provinces:
            prov = Province.objects.create(name=province[0])
            for municipality in province[1]:
                _ = Municipality.objects.create(name=municipality, province_id=prov.id)

    def create_notification_types(self) -> None:
        """Creates all notification types objects"""

        self.stdout.write(self.style.NOTICE("start populating notification types"))

        notification_types = [
            ("Informativo", "info", "mdi-information-outline"),
            ("Promocional", "info", "mdi-tag-outline"),
            ("Recordatorio", "info", "mdi-bell-outline"),
        ]

        for notification_type in notification_types:
            _ = NotificationType.objects.get_or_create(
                name=notification_type[0],
                color=notification_type[1],
                icon=notification_type[2],
            )

    def create_roles(self) -> None:
        """Creates all rol objects"""

        self.stdout.write(self.style.NOTICE("start populating roles"))

        roles = ["Administrador", "Comercial", "Económico"]

        permissions = Permission.objects.all()
        for role in roles:
            role_group, _ = Group.objects.get_or_create(name=role)
            if role == "Administrador":
                for permission in permissions:
                    role_group.permissions.add(permission)

    def create_brands(self) -> None:
        """Creates all brands objects"""

        self.stdout.write(self.style.NOTICE("start populating brands"))

        brands = [
            ("TYSON", "brands/pics/afro_love.png"),
            ("HOUSE OF RAEFORD", "brands/pics/afro_love.png"),
            ("UNCLE SAM", "brands/pics/afro_love.png"),
            ("ATLANTIKO", "brands/pics/afro_love.png"),
            ("VIMA", "brands/pics/afro_love.png"),
        ]

        for brand in brands:
            _ = Brand.objects.get_or_create(name=brand[0], logo_brand=brand[1])

    def create_products(self) -> None:
        """Creates all product´s objects"""

        self.stdout.write(self.style.NOTICE("start populating products"))

        products = [
            (
                "FC-0001",  # code_sku
                "Arroz PREMIUM",  # name
                "5000",  # quantity
                29.4,  # unit_price
                20.55,  # cost_price
                "USD",  # currency
                30,  # quantity_per_box
                "Arroz",  # category
                "UNCLE SAM",  # provider
                "UNCLE SAM",  # brand
                "USA",  # country
                "PACA",  # measurement_unit
            ),
            (
                "FC-0002",  # code_sku
                "Atún en aceite",  # name
                "15000",  # quantity
                35.2,  # unit_price
                30.55,  # cost_price
                "USD",  # currency
                48,  # quantity_per_box
                "Atún",  # category
                "ATLANTIKO",  # provider
                "ATLANTIKO",  # brand
                "USA",  # country
                "CAJA",  # measurement_unit
            ),
            (
                "FC-0003",  # code_sku
                "Huevos importados",  # name
                "50000",  # quantity
                53.4,  # unit_price
                49.15,  # cost_price
                "USD",  # currency
                12,  # quantity_per_box
                "Huevos",  # category
                None,  # provider
                None,  # brand
                "USA",  # country
                "CAJA",  # measurement_unit
            ),
            (
                "FC-0004",  # code_sku
                "Pollo 40 libras",  # name
                "25000",  # quantity
                30.3,  # unit_price
                20.55,  # cost_price
                "USD",  # currency
                1,  # quantity_per_box
                "Pollos",  # category
                "HOUSE OF RAEFORD",  # provider
                "HOUSE OF RAEFORD",  # brand
                "USA",  # country
                "CAJA",  # measurement_unit
            ),
        ]

        for product in products:
            _ = Product.objects.get_or_create(
                code_sku=product[0],
                name=product[1],
                slug=slugify(product[1]),
                quantity=product[2],
                unit_price=product[3],
                cost_price=product[4],
                quantity_per_box=product[6],
                category=Category.objects.get(name=product[7]),
                provider=(
                    Provider.objects.get(name=product[8])
                    if product[8] is not None
                    else None
                ),
                brand=(
                    Brand.objects.get(name=product[9])
                    if product[9] is not None
                    else None
                ),
                country=Country.objects.get(code_alpha3=product[10]),
                measurement_unit=Measurement_Unit.objects.get(name=product[11]),
            )

    def create_users(self):
        """Creates all users object"""

        self.stdout.write(self.style.NOTICE("start populating users"))

        user = User(
            first_name="Comercial",
            last_name="FEROS GRUPO S.U.R.L.",
            email="comercial@gmail.com",
            phone_number=None,
            check_terms_conditions=True,
            check_privacy_policy=True,
            is_staff=True,
            is_superuser=False,
            is_active=True,
            verified=True,
            is_deliverer=True,
        )
        user.set_password("123456")
        user.save()
        user.groups.add(Group.objects.get(name="Comercial"))

        _ = User(
            first_name="Administrador",
            last_name="FEROS GRUPO S.U.R.L.",
            email="administrador@gmail.com",
            phone_number="",
            check_terms_conditions=True,
            check_privacy_policy=True,
            is_staff=True,
            is_superuser=False,
            is_active=True,
            verified=True,
        )
        _.set_password("123456")
        _.save()
        _.groups.add(Group.objects.get(name="Administrador"))

        cliente = User(
            first_name="Cliente",
            last_name="FEROS GRUPO S.U.R.L.",
            email="cliente@gmail.com",
            address="Primera y 114, Playa, La Habana",
            phone_number="",
            check_terms_conditions=True,
            check_privacy_policy=True,
            next_login_change_password=False,
            newsletter=False,
            is_staff=False,
            is_superuser=False,
            is_active=True,
            verified=True,
        )
        cliente.set_password("123456")
        cliente.save()
        Wallet.objects.create(user=cliente, amount=100)

        _ = User(
            first_name="Carlos R.",
            last_name="González Jiménez",
            email="cranza@gmail.com",
            phone_number="",
            check_terms_conditions=True,
            check_privacy_policy=True,
            next_login_change_password=False,
            newsletter=True,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            verified=True,
        )
        _.set_password("123456")
        _.save()
        _.groups.add(Group.objects.get(name="Administrador"))

        _ = User(
            first_name="Pavel",
            last_name="Peréz",
            email="perezpavel5426@gmail.com",
            phone_number=None,
            check_terms_conditions=True,
            check_privacy_policy=True,
            next_login_change_password=False,
            newsletter=True,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            verified=True,
        )
        _.set_password("123456")
        _.save()
        _.groups.add(Group.objects.get(name="Administrador"))

    def run_seed(self):
        """Seed database"""

        self.stdout.write(self.style.WARNING("flushing database..."))
        call_command("flush", no_input=False)
        self.stdout.write(self.style.WARNING("checking migrations..."))
        call_command("makemigrations")
        self.stdout.write(self.style.WARNING("migrating..."))
        call_command("migrate")

        self.create_configuration()
        self.create_categories()
        self.create_roles()
        self.create_users()
        self.create_brands()
        self.create_provinces()
        self.create_order_statuses()
        self.create_currencies()
        self.create_countries()
        self.create_measurement_units()
        self.create_notification_types()
        self.create_providers()
        self.create_specifications()
        self.create_cms_infrastructure()
        self.create_blog_tags()
        self.create_blog_categories()
        self.create_shipping_zones()
        self.create_shipping_methods()
        self.create_shipping_rates()
        self.create_payment_methods()
        self.create_post()
        self.create_products()
