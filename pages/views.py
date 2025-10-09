from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from products.models import Category, Product


class HomePageView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ---------- Hero slider ----------
        if not context.get("hero_slides"):
            context["hero_slides"] = [
                {
                    "image": static("img/slider/banner1.jpg"),
                    "title": "خیریه‌ی ما",
                    "subtitle": "به فروشگاه خیریه هیوا خوش آمدید! هر خرید شما حامی خانواده‌ها و کودکان نیازمند است.",
                    "btn_text": "مشاهده محصولات",
                    "btn_link": "#products",
                },
                {
                    "image": static("img/slider/banner2.jpg"),
                    "title": "حمایت از نیازمندان",
                    "subtitle": "درآمد فروش محصولات صرف تامین هزینه‌های آموزشی، درمانی و معیشتی خانواده‌ها می‌شود.",
                    "btn_text": "همین حالا کمک کنید",
                    "btn_link": "#charity",
                },
                {
                    "image": static("img/slider/banner3.jpg"),
                    "title": "محصولات دست‌ساز",
                    "subtitle": "محصولات با کیفیتی که توسط توان‌یاب‌ها و مادران سرپرست خانوار تولید شده‌اند.",
                    "btn_text": "مشاهده محصولات",
                    "btn_link": "#products",
                },
            ]

        # ---------- Intro cards ----------
        if not context.get("intro_cards"):
            context["intro_cards"] = [
                {
                    "icon": "fas fa-heart",
                    "title": "ماموریت ما",
                    "text": "پشتیبانی از کودکان بی‌سرپرست و خانواده‌های نیازمند از طریق ایجاد اشتغال و فروش محصولات.",
                },
                {
                    "icon": "fas fa-hands-helping",
                    "title": "چگونه کمک می‌کنیم؟",
                    "text": "درآمد حاصل از فروش مستقیماً صرف تهیه مایحتاج، درمان و آموزش خانواده‌های تحت پوشش می‌شود.",
                },
                {
                    "icon": "fas fa-users",
                    "title": "جامعه هیوا",
                    "text": "بیش از ۵۰۰ خانواده و ۲۰۰ کودک تاکنون با همراهی شما از خدمات هیوا بهره‌مند شده‌اند.",
                },
            ]

        # ---------- Products ----------
        product_categories = []
        foods_products = Product.objects.none()
        bags_products = Product.objects.none()

        for slug, title, url_name in (
            ("foods", "محصولات خوراکی", "products:foods_list"),
            ("bags", "کیف‌ها", "products:bags_list"),
        ):
            category = Category.objects.filter(slug=slug).first()
            if not category:
                continue

            products = (
                Product.objects.filter(
                    category=category,
                    is_active=True,
                    inventory__gt=0,
                )
                .order_by("-datetime_created")[:4]
            )

            product_categories.append(
                {
                    "name": title,
                    "url": self._safe_reverse(url_name),
                    "products": products,
                }
            )

            if slug == "foods":
                foods_products = products
            elif slug == "bags":
                bags_products = products

        context["product_categories"] = product_categories
        context["foods_products"] = foods_products
        context["bags_products"] = bags_products

        # ---------- Charity ----------
        if not context.get("charity"):
            context["charity"] = {
                "title": "انجمن یاوران گل نرگس",
                "description": "تمرکز ما حمایت همه‌جانبه از کودکان بی‌سرپرست و کم‌توان است؛ از آموزش و درمان تا معیشت و مشاوره.",
                "url": self._safe_reverse("charity:charity", fallback="#"),
                "cards": [
                    {"title": "حمایت تحصیلی", "text": "تامین شهریه و لوازم تحریر برای دانش‌آموزان تحت پوشش."},
                    {"title": "بسته‌های معیشتی", "text": "توزیع منظم بسته‌های غذایی و بهداشتی بین خانواده‌ها."},
                    {"title": "کارگاه‌های مهارتی", "text": "آموزش مهارت‌های شغلی برای مادران و جوانان خانواده‌ها."},
                    {"title": "پشتیبانی روانشناسی", "text": "ارائه خدمات مشاوره و روان‌درمانی رایگان به کودکان."},
                ],
            }

        return context

    @staticmethod
    def _safe_reverse(route_name: str, fallback: str = "#") -> str:
        try:
            return reverse(route_name)
        except NoReverseMatch:
            return fallback


class AboutUsView(TemplateView):
    template_name = 'pages/aboutus.html'


class ContactUsView(TemplateView):
    template_name = 'pages/contactus.html'
