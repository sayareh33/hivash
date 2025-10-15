from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from products.models import Category, Product

# pages/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ContactMessageForm

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

        for slug, title in (
            ("foods", "U.O-O?U^U,OO? OrU^O?OUcUO"),
            ("bags", "UcUOU???OU?O"),
        ):
            category = Category.objects.filter(slug=slug).first()
            if not category:
                continue

            category_ids = [category.id]
            child_ids = list(
                Category.objects.filter(parent=category, is_active=True).values_list("id", flat=True)
            )
            while child_ids:
                category_ids.extend(child_ids)
                child_ids = list(
                    Category.objects.filter(parent__in=child_ids, is_active=True).values_list("id", flat=True)
                )

            products = (
                Product.objects.filter(
                    category_id__in=category_ids,
                    is_active=True,
                    status="published",
                    inventory__gt=0,
                )
                .order_by("-datetime_created")[:4]
            )

            product_categories.append(
                {
                    "name": title,
                    "url": f"{self._safe_reverse('products:product_list')}?category={category.slug}",
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
                "url": self._safe_reverse("charity:home", fallback="#"),
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


@login_required(login_url='accounts:login')
def contactus_view(request):
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            contact_message.user = request.user
            contact_message.save()
            messages.success(request, 'پیام شما با موفقیت ارسال شد. سپاس از همراهی شما 🌱')
            return redirect('pages:contactus')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را برطرف کنید.')
    else:
        form = ContactMessageForm()

    return render(request, 'pages/contactus.html', {'form': form})



# class ContactView(LoginRequiredMixin, CreateView):
#     model = ContactMessage
#     form_class = ContactForm
#     template_name = 'pages/contactus.html'
#     success_url = reverse_lazy('pages:contactus')
#     login_url = '/accounts/login/'  # Adjust to your login URL
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['user'] = self.request.user
#         return kwargs
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         # Get site settings
#         try:
#             site_settings = SiteSetting.objects.first()
#         except SiteSetting.DoesNotExist:
#             site_settings = SiteSetting.objects.create(
#                 site_name="هیوا عشقال",
#                 contact_email="info@hiva-eshghal.ir",
#                 support_email="support@hiva-eshghal.ir",
#                 phone_number="07134567890",
#                 mobile_number="09384501026",
#                 address="استان فارس، شهرستان قیر و کارزین، قیر، کوچه سه شهید",
#                 sat_to_wed_hours="8:00 - 17:00",
#                 thursday_hours="8:00 - 14:00",
#                 friday_hours="تعطیل",
#                 map_embed_url="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3456.789012345678!2d51.12345678901234!3d29.98765432109876!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjnCsDU5JzE1LjYiTiA1McKwMDcnMjguNiJF!5e0!3m2!1sen!2sir!4v1234567890123!5m2!1sen!2sir"
#             )
#
#         context['site_settings'] = site_settings
#         return context
#
#     def form_valid(self, form):
#         # Get IP address
#         x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
#         if x_forwarded_for:
#             ip = x_forwarded_for.split(',')[0]
#         else:
#             ip = self.request.META.get('REMOTE_ADDR')
#
#         # Set the user and IP address
#         form.instance.user = self.request.user
#         form.instance.ip_address = ip
#
#         response = super().form_valid(form)
#
#         messages.success(
#             self.request,
#             _('پیام شما با موفقیت ارسال شد. در اسرع وقت با شما تماس خواهیم گرفت.')
#         )
#         return response
#
#     def form_invalid(self, form):
#         messages.error(
#             self.request,
#             _('خطایی در ارسال پیام رخ داد. لطفاً اطلاعات را بررسی کرده و مجدداً تلاش کنید.')
#         )
#         return super().form_invalid(form)


# Function-based view with authentication
from django.contrib.auth.decorators import login_required

#
# @login_required
# def contact_view(request):
#     site_settings = SiteSetting.objects.first()
#
#     if not site_settings:
#         site_settings = SiteSetting.objects.create(
#             site_name="هیوا عشقال",
#             contact_email="info@hiva-eshghal.ir",
#             support_email="support@hiva-eshghal.ir",
#             phone_number="07134567890",
#             mobile_number="09384501026",
#             address="استان فارس، شهرستان قیر و کارزین، قیر، کوچه سه شهید",
#             sat_to_wed_hours="8:00 - 17:00",
#             thursday_hours="8:00 - 14:00",
#             friday_hours="تعطیل",
#             map_embed_url="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3456.789012345678!2d51.12345678901234!3d29.98765432109876!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2zMjnCsDU5JzE1LjYiTiA1McKwMDcrMjguNiJF!5e0!3m2!1sen!2sir!4v1234567890123!5m2!1sen!2sir"
#         )
#
#     if request.method == 'POST':
#         form = ContactForm(request.POST, user=request.user)
#         if form.is_valid():
#             # Get IP address
#             x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#             if x_forwarded_for:
#                 ip = x_forwarded_for.split(',')[0]
#             else:
#                 ip = request.META.get('REMOTE_ADDR')
#
#             contact_message = form.save(commit=False)
#             contact_message.user = request.user
#             contact_message.ip_address = ip
#             contact_message.save()
#
#             messages.success(
#                 request,
#                 _('پیام شما با موفقیت ارسال شد. در اسرع وقت با شما تماس خواهیم گرفت.')
#             )
#             return redirect('pages:contactus')
#         else:
#             messages.error(
#                 request,
#                 _('خطایی در ارسال پیام رخ داد. لطفاً اطلاعات را بررسی کرده و مجدداً تلاش کنید.')
#             )
#     else:
#         form = ContactForm(user=request.user)
#
#     context = {
#         'form': form,
#         'site_settings': site_settings,
#     }
#
#     return render(request, 'pages/contactus.html', context)



# def contact_us(request):
#     if request.method == 'POST':
#         form = ContactUsForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'پیام شما با موفقیت ارسال شد.')
#             return redirect('contact_us')
#         else:
#             messages.error(request, 'لطفا فرم را به درستی پر کنید.')
#     else:
#         form = ContactUsForm()
#
#     return render(request, 'contact/contact_us.html', {
#         'form': form,
#     })

