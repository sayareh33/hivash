import jdatetime
from django.contrib import admin
from django.utils import timezone
from django_jalali.admin.filters import JDateFieldListFilter

from .models import Order, OrderItem


class OrderItemInLine(admin.TabularInline):  # (or)(admin.StackedInLine)
    model = OrderItem
    fields = ['order', 'product', 'quantity', 'price', ]
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer', 'jalali_datetime_created', 'is_paid']
    list_filter = ['is_paid', ('datetime_created', JDateFieldListFilter)]

    inlines = [
        OrderItemInLine,
     ]

    def jalali_datetime_created(self, obj):
        """Display creation timestamp using the Jalali calendar."""
        value = obj.datetime_created
        if value is None:
            return '-'
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return jdatetime.datetime.fromgregorian(datetime=value).strftime('%Y/%m/%d %H:%M')

    jalali_datetime_created.short_description = 'Created (Jalali)'
    jalali_datetime_created.admin_order_field = 'datetime_created'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', ]
