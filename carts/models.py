from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


class ShippingMethod(models.Model):
    """Configurable shipping option with a fixed base fee."""

    name = models.CharField(_("نام روش ارسال"), max_length=120, unique=True)
    description = models.TextField(_("توضیحات"), blank=True)
    base_cost = models.DecimalField(
        _("هزینه پایه"),
        max_digits=10,
        decimal_places=0,
        default=Decimal("0"),
        help_text=_("مبلغ ثابتی که به مجموع سفارش اضافه می‌شود."),
    )
    is_active = models.BooleanField(_("فعال؟"), default=True)
    is_default = models.BooleanField(
        _("روش پیش‌فرض؟"),
        default=False,
        help_text=_("در صورت انتخاب، به صورت خودکار برای سبدهای جدید لحاظ می‌شود."),
    )
    minimum_order_total = models.DecimalField(
        _("حداقل مبلغ سفارش"),
        max_digits=12,
        decimal_places=0,
        default=Decimal("0"),
        help_text=_("در صورت تعیین، فقط برای سفارش‌هایی با مجموع برابر یا بیشتر از این مقدار اعمال می‌شود."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "base_cost", "name"]
        verbose_name = _("روش ارسال")
        verbose_name_plural = _("روش‌های ارسال")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.name

    def clean(self):
        """Ensure only a single default shipping method exists."""
        super().clean()
        if self.is_default:
            ShippingMethod.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
