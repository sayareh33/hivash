from django.shortcuts import render
from django.views.generic import TemplateView

from products.models import Category, Product


class HomePageView(TemplateView):
    template_name = 'pages/home.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        foods_category = Category.objects.filter(slug='foods').first()
        bags_category = Category.objects.filter(slug='bags').first()  # اصلاح این خط

        # محصولات دسته‌بندی خوراکی‌ها
        if foods_category:
            context['foods_products'] = Product.objects.filter(
                category=foods_category,
                is_active=True,
                inventory__gt=0  # اضافه کردن شرط موجودی
            )[:4]
        else:
            context['foods_products'] = Product.objects.none()

        # محصولات دسته‌بندی کیف‌ها
        if bags_category:
            context['bags_products'] = Product.objects.filter(
                category=bags_category,
                is_active=True,
                inventory__gt=0  # اضافه کردن شرط موجودی
            )[:4]
        else:
            context['bags_products'] = Product.objects.none()

        return context


class AboutUsView(TemplateView):
    template_name = 'pages/aboutus.html'

class ContactUsView(TemplateView):
    template_name = 'pages/contactus.html'