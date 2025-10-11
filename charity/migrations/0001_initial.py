from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ImpactStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120, verbose_name='عنوان')),
                ('value', models.CharField(max_length=120, verbose_name='مقدار')),
                ('unit', models.CharField(blank=True, max_length=60, verbose_name='واحد')),
                ('description', models.TextField(blank=True, verbose_name='توضیح تکمیلی')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'آمار اثرگذاری',
                'verbose_name_plural': 'آمارهای اثرگذاری',
                'ordering': ['display_order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='ParticipationMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='عنوان')),
                ('slug', models.SlugField(max_length=160, unique=True, verbose_name='نامک')),
                ('description', models.TextField(verbose_name='توضیحات')),
                ('icon', models.CharField(blank=True, max_length=50, verbose_name='کلاس آیکن (Bootstrap/Icon)')),
                ('action_text', models.CharField(blank=True, max_length=80, verbose_name='متن دکمه اقدام')),
                ('action_url', models.URLField(blank=True, verbose_name='لینک اقدام')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'روش مشارکت',
                'verbose_name_plural': 'روش‌های مشارکت',
                'ordering': ['display_order', 'title'],
            },
        ),
        migrations.CreateModel(
            name='ProjectGallery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media_type', models.CharField(choices=[('image', 'تصویر'), ('video', 'ویدئو'), ('external', 'لینک خارجی')], default='image', max_length=20, verbose_name='نوع رسانه')),
                ('image', models.ImageField(blank=True, null=True, upload_to='charity/projects/gallery/images/', verbose_name='فایل تصویر')),
                ('video_file', models.FileField(blank=True, null=True, upload_to='charity/projects/gallery/videos/', verbose_name='فایل ویدئو')),
                ('external_url', models.URLField(blank=True, verbose_name='لینک خارجی')),
                ('caption', models.CharField(blank=True, max_length=200, verbose_name='عنوان')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'رسانه پروژه',
                'verbose_name_plural': 'رسانه‌های پروژه',
                'ordering': ['display_order', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CharityProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان پروژه')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='نامک')),
                ('short_description', models.CharField(max_length=300, verbose_name='توضیح کوتاه')),
                ('full_description', models.TextField(verbose_name='توضیحات کامل')),
                ('impact_summary', models.CharField(blank=True, max_length=255, verbose_name='جمع‌بندی اثرگذاری')),
                ('status', models.CharField(choices=[('upcoming', 'در حال برنامه‌ریزی'), ('active', 'در حال اجرا'), ('completed', 'تکمیل شده'), ('archived', 'آرشیو شده')], default='active', max_length=20, verbose_name='وضعیت')),
                ('location', models.CharField(blank=True, max_length=150, verbose_name='مکان اجرا')),
                ('beneficiaries_count', models.PositiveIntegerField(blank=True, null=True, verbose_name='تعداد ذی‌نفعان')),
                ('hero_video_url', models.URLField(blank=True, verbose_name='لینک ویدئوی معرفی')),
                ('target_amount', models.DecimalField(decimal_places=0, max_digits=15, validators=[django.core.validators.MinValueValidator(1000)], verbose_name='مبلغ هدف (تومان)')),
                ('current_amount', models.DecimalField(decimal_places=0, default=0, max_digits=15, verbose_name='مبلغ جمع‌آوری‌شده فعلی (تومان)')),
                ('start_date', models.DateField(verbose_name='تاریخ شروع')),
                ('end_date', models.DateField(verbose_name='تاریخ پایان')),
                ('completion_date', models.DateField(blank=True, null=True, verbose_name='تاریخ تکمیل')),
                ('is_featured', models.BooleanField(default=False, verbose_name='نمایش ویژه')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('image', models.ImageField(upload_to='charity/projects/', verbose_name='تصویر شاخص')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('gallery', models.ManyToManyField(blank=True, related_name='projects', to='charity.projectgallery', verbose_name='رسانه‌های پروژه')),
            ],
            options={
                'verbose_name': 'پروژه حمایتی',
                'verbose_name_plural': 'پروژه‌های حمایتی',
                'ordering': ['-is_featured', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=0, max_digits=15, validators=[django.core.validators.MinValueValidator(1000)], verbose_name='مبلغ کمک (تومان)')),
                ('payment_status', models.CharField(choices=[('pending', 'در انتظار پرداخت'), ('paid', 'پرداخت‌شده'), ('failed', 'ناموفق'), ('refunded', 'بازپرداخت‌شده'), ('canceled', 'لغوشده'), ('expired', 'منقضی‌شده'), ('processing', 'در حال پردازش')], default='pending', max_length=20, verbose_name='وضعیت پرداخت')),
                ('payment_gateway', models.CharField(blank=True, choices=[('zarinpal', 'زرین‌پال'), ('saman', 'سامان'), ('paypal', 'پی‌پل'), ('idpay', 'آی‌دی‌پی'), ('manual', 'دستی')], max_length=20, null=True, verbose_name='درگاه پرداخت')),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='شناسه تراکنش')),
                ('donor_name', models.CharField(blank=True, max_length=150, verbose_name='نام حامی')),
                ('donor_email', models.EmailField(blank=True, max_length=254, verbose_name='ایمیل حامی')),
                ('donor_phone', models.CharField(blank=True, max_length=20, verbose_name='شماره تماس')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='نمایش ناشناس')),
                ('message', models.CharField(blank=True, max_length=300, verbose_name='پیام حامی')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('donor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='donations', to=settings.AUTH_USER_MODEL, verbose_name='حامی')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='donations', to='charity.charityproject', verbose_name='پروژه')),
            ],
            options={
                'verbose_name': 'کمک مالی',
                'verbose_name_plural': 'کمک‌های مالی',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProjectUpdate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان به‌روزرسانی')),
                ('summary', models.CharField(blank=True, max_length=300, verbose_name='خلاصه')),
                ('body', models.TextField(verbose_name='متن کامل')),
                ('progress_percent', models.PositiveIntegerField(blank=True, null=True, verbose_name='درصد پیشرفت')),
                ('highlight_image', models.ImageField(blank=True, null=True, upload_to='charity/projects/updates/images/', verbose_name='تصویر اصلی')),
                ('video_file', models.FileField(blank=True, null=True, upload_to='charity/projects/updates/videos/', verbose_name='فایل ویدئو')),
                ('video_url', models.URLField(blank=True, verbose_name='لینک ویدئو')),
                ('is_public', models.BooleanField(default=True, verbose_name='قابل نمایش در سایت')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('published_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='تاریخ انتشار')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updates', to='charity.charityproject', verbose_name='پروژه')),
            ],
            options={
                'verbose_name': 'به‌روزرسانی پروژه',
                'verbose_name_plural': 'به‌روزرسانی‌های پروژه',
                'ordering': ['display_order', '-published_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=0, max_digits=15, verbose_name='مبلغ')),
                ('status', models.CharField(choices=[('pending', 'در انتظار پرداخت'), ('paid', 'پرداخت‌شده'), ('failed', 'ناموفق'), ('refunded', 'بازپرداخت‌شده'), ('canceled', 'لغوشده'), ('expired', 'منقضی‌شده'), ('processing', 'در حال پردازش')], max_length=20, verbose_name='وضعیت')),
                ('gateway', models.CharField(choices=[('zarinpal', 'زرین‌پال'), ('saman', 'سامان'), ('paypal', 'پی‌پل'), ('idpay', 'آی‌دی‌پی'), ('manual', 'دستی')], max_length=20, verbose_name='درگاه پرداخت')),
                ('transaction_code', models.CharField(max_length=100, verbose_name='کد تراکنش')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('raw_response', models.JSONField(blank=True, null=True, verbose_name='پاسخ خام درگاه')),
                ('donation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='charity.donation', verbose_name='کمک مالی')),
            ],
            options={
                'verbose_name': 'تراکنش پرداخت',
                'verbose_name_plural': 'تراکنش‌های پرداخت',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DonationReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_number', models.CharField(max_length=50, unique=True, verbose_name='شماره رسید')),
                ('issued_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ صدور')),
                ('pdf_file', models.FileField(upload_to='donations/receipts/pdf/', verbose_name='فایل PDF')),
                ('donation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='donation_receipt', to='charity.donation', verbose_name='کمک مالی')),
            ],
            options={
                'verbose_name': 'رسید کمک',
                'verbose_name_plural': 'رسیدهای کمک',
                'ordering': ['-issued_at'],
            },
        ),
    ]
