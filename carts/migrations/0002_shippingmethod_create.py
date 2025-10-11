from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("carts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShippingMethod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="نام روش ارسال")),
                ("description", models.TextField(blank=True, verbose_name="توضیحات")),
                (
                    "base_cost",
                    models.DecimalField(
                        decimal_places=0,
                        default=Decimal("0"),
                        max_digits=10,
                        verbose_name="هزینه پایه",
                        help_text="مبلغ ثابت که به مجموع سفارش اضافه می‌شود.",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="فعال؟")),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="در صورت انتخاب، به صورت خودکار برای سبدهای جدید لحاظ می‌شود.",
                        verbose_name="روش پیش‌فرض؟",
                    ),
                ),
                (
                    "minimum_order_total",
                    models.DecimalField(
                        decimal_places=0,
                        default=Decimal("0"),
                        help_text="در صورت تعیین، فقط برای سفارش‌هایی با مجموع برابر یا بیشتر از این مقدار اعمال می‌شود.",
                        max_digits=12,
                        verbose_name="حداقل مبلغ سفارش",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-is_default", "base_cost", "name"],
                "verbose_name": "روش ارسال",
                "verbose_name_plural": "روش‌های ارسال",
            },
        ),
    ]
