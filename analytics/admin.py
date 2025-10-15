from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from .models import Visit
from django.db.models.functions import TruncDate

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    # ستون‌هایی که در لیست نمایش داده می‌شوند
    list_display = (
        'created_at',
        'user_display',
        'path',
        'method',
        'ip_address',
        'country',
        'city',
        'device',
        'browser',
    )

    # فیلتر برای راحتی جستجو
    list_filter = (
        'country',
        'device',
        'browser',
        'created_at',
    )

    # فیلدهایی که قابل جستجو هستند
    search_fields = (
        'ip_address',
        'user__phone',
        'path',
        'country',
        'city',
        'device',
        'browser',
    )

    # فیلد تاریخ برای ناوبری راحت‌تر
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    # نمایش نمودار و آمار در بالای change_list
    change_list_template = 'admin/visits_change_list.html'

    def user_display(self, obj):
        if obj.user:
            return obj.user.username
        return 'مهمان'
    user_display.short_description = 'کاربر'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # آمار روزانه 7 روز گذشته
        stats = (
            Visit.objects
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(total=Count('id'))
            .order_by('-date')[:7]
        )
        daily_data = {item['date'].strftime('%Y-%m-%d'): item['total'] for item in stats}

        extra_context['chart_data'] = daily_data
        extra_context['total_visits'] = Visit.objects.count()
        extra_context['unique_ips'] = Visit.objects.values('ip_address').distinct().count()

        return super().changelist_view(request, extra_context=extra_context)
