from django.contrib import admin

from .models import (
    CharityProject,
    ProjectGallery,
    ProjectUpdate,
    ParticipationMethod,
    ImpactStat,
    Donation,
    DonationReceipt,
    PaymentTransaction,
)


@admin.register(ProjectGallery)
class ProjectGalleryAdmin(admin.ModelAdmin):
    list_display = ('id', 'caption', 'media_type', 'display_order', 'created_at')
    list_filter = ('media_type',)
    search_fields = ('caption',)
    ordering = ('display_order', '-created_at')


class ProjectGalleryInline(admin.TabularInline):
    model = CharityProject.gallery.through
    extra = 1
    verbose_name = 'رسانه'
    verbose_name_plural = 'رسانه‌های پروژه'


@admin.register(CharityProject)
class CharityProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'status',
        'is_featured',
        'is_active',
        'target_amount',
        'current_amount',
        'progress',
        'start_date',
        'end_date',
    )
    list_filter = ('status', 'is_featured', 'is_active')
    search_fields = ('title', 'short_description', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProjectGalleryInline]
    filter_horizontal = ('gallery',)
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'short_description', 'full_description', 'impact_summary')}),
        ('اطلاعات اجرا', {
            'fields': (
                'status',
                'is_featured',
                'is_active',
                'location',
                'beneficiaries_count',
                'hero_video_url',
            )
        }),
        ('مالی', {'fields': ('target_amount', 'current_amount')}),
        ('زمان‌بندی', {'fields': ('start_date', 'end_date', 'completion_date')}),
        ('رسانه', {'fields': ('image', 'gallery')}),
    )


@admin.register(ProjectUpdate)
class ProjectUpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'progress_percent', 'is_public', 'published_at')
    list_filter = ('is_public', 'project')
    search_fields = ('title', 'summary', 'project__title')
    ordering = ('project', 'display_order', '-published_at')


@admin.register(ParticipationMethod)
class ParticipationMethodAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('display_order', 'title')


@admin.register(ImpactStat)
class ImpactStatAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'unit', 'is_active', 'display_order')
    list_filter = ('is_active',)
    ordering = ('display_order', 'title')


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'amount', 'payment_status', 'donor', 'is_anonymous', 'created_at')
    list_filter = ('payment_status', 'payment_gateway', 'is_anonymous', 'project')
    search_fields = ('donor_name', 'donor_email', 'transaction_id')
    autocomplete_fields = ('project', 'donor')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DonationReceipt)
class DonationReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'donation', 'issued_at')
    search_fields = ('receipt_number', 'donation__donor_name')
    readonly_fields = ('issued_at',)


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'donation', 'amount', 'status', 'gateway', 'created_at')
    list_filter = ('status', 'gateway')
    search_fields = ('transaction_code',)
    readonly_fields = ('created_at', 'updated_at')
