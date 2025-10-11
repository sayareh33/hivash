from django.db.models import Prefetch, Q, Sum
from django.http import Http404
from django.views.generic import DetailView, ListView, TemplateView

from .forms import DonationForm
from .models import (
    CharityProject,
    Donation,
    ImpactStat,
    ParticipationMethod,
    PaymentStatus,
    ProjectGallery,
    ProjectUpdate,
)

class CharityHomeView(TemplateView):
    """Landing page that introduces the charity programs."""

    template_name = 'charity/charity_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        featured_projects = (
            CharityProject.objects.filter(is_active=True)
            .prefetch_related('gallery')
            .order_by('-is_featured', 'start_date')[:3]
        )

        active_projects_queryset = (
            CharityProject.objects.filter(
                is_active=True,
                status__in=[
                    CharityProject.ProjectStatus.ACTIVE,
                    CharityProject.ProjectStatus.UPCOMING,
                ],
            )
            .prefetch_related('gallery')
            .order_by('start_date')
        )

        spotlight_projects = list(active_projects_queryset[:3])
        if not spotlight_projects:
            spotlight_projects = list(featured_projects[:3])

        spotlight_ids = [project.id for project in spotlight_projects]
        remaining_projects_queryset = (
            active_projects_queryset.exclude(id__in=spotlight_ids)
            if spotlight_ids
            else active_projects_queryset
        )
        active_projects = list(remaining_projects_queryset[:6])

        completed_projects_queryset = (
            CharityProject.objects.filter(status=CharityProject.ProjectStatus.COMPLETED)
            .order_by('-completion_date', '-updated_at')
        )
        completed_projects = list(completed_projects_queryset[:4])

        impact_stats = ImpactStat.objects.filter(is_active=True).order_by('display_order')
        participation_methods = ParticipationMethod.objects.filter(
            is_active=True
        ).order_by('display_order')

        total_raised = (
            Donation.objects.filter(payment_status=PaymentStatus.PAID)
            .aggregate(total=Sum('amount'))['total']
            or 0
        )
        donor_count = (
            Donation.objects.filter(payment_status=PaymentStatus.PAID, donor__isnull=False)
            .values('donor')
            .distinct()
            .count()
        )
        contributions_count = (
            Donation.objects.filter(payment_status=PaymentStatus.PAID).count()
        )
        average_gift = total_raised / contributions_count if contributions_count else 0

        latest_updates = (
            ProjectUpdate.objects.filter(is_public=True)
            .select_related('project')
            .order_by('-published_at')[:3]
        )

        highlight_stats = [
            {
                'label': 'پروژه فعال و در دست اجرا',
                'value': active_projects_queryset.count(),
                'format': 'number',
                'accent': 'teal',
                'icon': 'bi-lightning-charge-fill',
            },
            {
                'label': 'پروژه به سرانجام رسیده',
                'value': completed_projects_queryset.count(),
                'format': 'number',
                'accent': 'forest',
                'icon': 'bi-check2-circle',
            },
            {
                'label': 'خیرین عضو پلتفرم',
                'value': donor_count,
                'format': 'number',
                'accent': 'violet',
                'icon': 'bi-people-heart',
            },
            {
                'label': 'مبلغ کل کمک‌های جمع‌آوری‌شده',
                'value': int(total_raised),
                'format': 'currency',
                'accent': 'sun',
                'icon': 'bi-graph-up-arrow',
            },
        ]

        faq_items = [
            {
                'question': 'کمک‌های نقدی دقیقاً در چه پروژه‌هایی هزینه می‌شود؟',
                'answer': 'برای هر پروژه صفحه‌ای شفاف با گزارش پیشرفت، تصویر و رسیدهای مالی آماده شده است. تا زمانی که پرداخت‌ها توسط واحد مالی تأیید نشوند، بودجه آزاد نمی‌شود و همه اسناد در پروفایل خیرین قابل مشاهده است.',
            },
            {
                'question': 'چطور مطمئن شوم کمک من به دست خانواده هدف رسیده است؟',
                'answer': 'پس از هر پرداخت، رسید الکترونیکی و پیامک دریافت می‌کنید و در بخش «پیگیری کمک‌ها» می‌توانید وضعیت بسته‌ها یا خدمات ارائه‌شده را لحظه‌ای ببینید. تیم میدانی نیز گزارش تصویری از توزیع تهیه می‌کند.',
            },
            {
                'question': 'آیا می‌توانم به صورت معنوی یا غیرمالی مشارکت کنم؟',
                'answer': 'بله؛ پویش‌های فرهنگی، ختم قرآن، صلوات و برنامه‌های دعای جمعی در دسترس است. همچنین می‌توانید به‌عنوان داوطلب در بسته‌بندی، بازدید یا تولید محتوا همراه ما باشید.',
            },
        ]

        cultural_initiatives = [
            {
                'title': 'ختم قرآن خانوادگی',
                'description': 'هر روز نیم جزء تلاوت کنید تا در پایان ماه، ختم کامل قرآن به نیت گره‌گشایی از کار مددجویان انجام شود. گزارش پیشرفت در پروفایل شما ثبت می‌شود.',
                'participation_count': 1840,
                'cta_text': 'شرکت در ختم قرآن',
                'cta_url': '#spiritual-engagements',
                'icon': 'bi-journal-richtext',
            },
            {
                'title': 'پویش هزار صلوات امید',
                'description': 'با ثبت نذر صلوات هفتگی، نیات خود را برای خانواده‌های در انتظار به اشتراک بگذارید و نتیجه پویش را در گزارش‌های معنوی هیوا دنبال کنید.',
                'participation_count': 2765,
                'cta_text': 'ثبت نذر صلوات',
                'cta_url': '#spiritual-engagements',
                'icon': 'bi-stars',
            },
            {
                'title': 'دعای توسل و زیارت عاشورا آنلاین',
                'description': 'هر هفته در جمع آنلاین خیرین شرکت کنید، نیت‌های خود را ثبت نمایید و فایل صوتی مراسم را پس از اجرا دریافت کنید.',
                'participation_count': 931,
                'cta_text': 'ثبت‌نام در مراسم هفتگی',
                'cta_url': '#spiritual-engagements',
                'icon': 'bi-heart-pulse',
            },
        ]

        giving_channels = [
            {
                'title': 'کمک آنلاین و انتقال بانکی',
                'description': 'پرداخت آنلاین درگاه‌های امن و دریافت شماره حساب ویژه خیریه برای اشخاص حقیقی و حقوقی.',
                'icon': 'bi-credit-card',
            },
            {
                'title': 'حمایت کالایی و خدماتی',
                'description': 'اهدای بسته معیشتی، تجهیزات آموزشی، لوازم منزل یا ارائه خدمات تخصصی مانند پزشکی و مشاوره.',
                'icon': 'bi-box-seam',
            },
            {
                'title': 'مشارکت فرهنگی و معنوی',
                'description': 'حضور در پویش‌های ختم قرآن و صلوات، تولید محتوا و روایتگری برای گسترش فرهنگ مهربانی.',
                'icon': 'bi-peace',
            },
            {
                'title': 'داوطلبی میدانی و تخصصی',
                'description': 'همراهی در بازدید از خانواده‌ها، بسته‌بندی اقلام، اردوهای جهادی یا ارائه تخصص حرفه‌ای در پشت صحنه.',
                'icon': 'bi-people',
            },
        ]

        donation_plans = [
            {
                'title': 'حمایت ماهانه',
                'amount': '۱۰۰,۰۰۰ تومان',
                'tagline': 'کمک پایدار برای تأمین هزینه‌های ضروری خانواده‌ها',
                'features': [
                    'گزارش عملکرد ماهانه در پروفایل شما',
                    'دعوت به گردهمایی سالانه خیرین',
                    'کارت حمایت ویژه با نام شما',
                ],
                'variant': 'emerald',
                'button': 'انتخاب حمایت ماهانه',
            },
            {
                'title': 'حمایت ویژه',
                'amount': '۵۰۰,۰۰۰ تومان',
                'tagline': 'تأثیر سریع برای پروژه‌های درمانی و فوری',
                'features': [
                    'گزارش اختصاصی از پروژه انتخابی',
                    'گواهی مشارکت رسمی',
                    'ذکر نام در فهرست حامیان پروژه',
                ],
                'variant': 'royal',
                'badge': 'پیشنهادی',
                'button': 'انتخاب حمایت ویژه',
            },
            {
                'title': 'حمایت اختصاصی',
                'amount': 'مبلغ دلخواه',
                'tagline': 'آزادانه مبلغ و پروژه منتخب خود را تعیین کنید',
                'features': [
                    'امکان انتخاب پروژه یا خانواده مشخص',
                    'دریافت گزارش تصویری از پیشرفت',
                    'قدردانی شخصی از سوی تیم هیوا',
                ],
                'variant': 'amber',
                'button': 'ثبت حمایت اختصاصی',
            },
        ]

        bank_accounts = [
            {
                'bank': 'بانک ملی',
                'card': '6037-9917-1234-5678',
                'iban': 'IR12 0120 0000 0000 1234 56',
                'holder': 'مؤسسه خیریه هیوا',
                'logo': 'img/banks/melli.png',
            },
            {
                'bank': 'بانک ملت',
                'card': '6104-3378-8765-4321',
                'iban': 'IR45 0120 0000 0000 8765 43',
                'holder': 'مؤسسه خیریه هیوا',
                'logo': 'img/banks/mellat.png',
            },
        ]

        success_stories = [
            {
                'name': 'محمد رضایی',
                'role': 'حامی از سال ۱۳۹۸',
                'quote': 'وقتی دیدم کمک ماهانه من چطور توانست درمان یک کودک را کامل کند، فهمیدم حتی کمک‌های کوچک هم می‌تواند معجزه بیافریند.',
                'image': 'img/testimonials/1.jpg',
            },
            {
                'name': 'فاطمه محمدی',
                'role': 'مادر یکی از کودکان تحت پوشش',
                'quote': 'بدون همراهی شما هرگز نمی‌توانستم هزینه‌های درمان پسرم را تأمین کنم. امروز او سالم است و این را مدیون دل‌های مهربان شما هستم.',
                'image': 'img/testimonials/2.jpg',
            },
            {
                'name': 'علی حسینی',
                'role': 'داوطلب پروژه‌های عمرانی',
                'quote': 'ساخت یک مدرسه با کمک مردم، زندگی یک روستا را متحول کرد. دیدن لبخند بچه‌ها انگار خستگی همه مسیر را از بین می‌برد.',
                'image': 'img/testimonials/3.jpg',
            },
        ]

        context.update(
            {
                'featured_projects': featured_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'spotlight_projects': spotlight_projects,
                'impact_stats': impact_stats,
                'participation_methods': participation_methods,
                'total_raised': total_raised,
                'active_projects_count': active_projects_queryset.count(),
                'completed_projects_count': completed_projects_queryset.count(),
                'donor_count': donor_count,
                'contributions_count': contributions_count,
                'average_gift': average_gift,
                'latest_updates': latest_updates,
                'faq_items': faq_items,
                'cultural_initiatives': cultural_initiatives,
                'giving_channels': giving_channels,
                'highlight_stats': highlight_stats,
                'donation_plans': donation_plans,
                'bank_accounts': bank_accounts,
                'success_stories': success_stories,
            }
        )
        return context

class ProjectListView(ListView):
    """Paginated list of projects filtered by status."""

    model = CharityProject
    template_name = 'charity/project_list.html'
    context_object_name = 'projects'
    paginate_by = 9

    def get_queryset(self):
        status = self.request.GET.get('status')
        queryset = CharityProject.objects.filter(is_active=True).prefetch_related('gallery')

        if status in dict(CharityProject.ProjectStatus.choices):
            queryset = queryset.filter(status=status)
        else:
            queryset = queryset.exclude(status=CharityProject.ProjectStatus.ARCHIVED)

        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(short_description__icontains=search)
            )

        sort = self.request.GET.get('sort')
        if sort == 'latest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'goal':
            queryset = queryset.order_by('-target_amount')
        else:
            queryset = queryset.order_by('status', 'start_date')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_term'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', '')
        context['status_choices'] = CharityProject.ProjectStatus.choices
        return context

class ProjectDetailView(DetailView):
    """Detailed page for a single project including progress and updates."""

    model = CharityProject
    template_name = 'charity/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        gallery_qs = ProjectGallery.objects.all()
        updates_qs = ProjectUpdate.objects.filter(is_public=True).order_by(
            'display_order', '-published_at'
        )
        return CharityProject.objects.prefetch_related(
            Prefetch('gallery', queryset=gallery_qs),
            Prefetch('updates', queryset=updates_qs),
        )

    def get_object(self, queryset=None):
        project = super().get_object(queryset)
        if not project.is_active and not self.request.user.is_staff:
            raise Http404('دسترسی به این پروژه برای شما مجاز نیست.')
        return project

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = context['project']

        donations = (
            project.donations.filter(payment_status=PaymentStatus.PAID)
            .select_related('donor')
            .order_by('-created_at')[:10]
        )

        related_projects = (
            CharityProject.objects.filter(is_active=True)
            .exclude(pk=project.pk)
            .order_by('-is_featured', 'start_date')[:3]
        )

        context.update(
            {
                'donations': donations,
                'donation_form': DonationForm(
                    user=self.request.user, initial={'project': project}
                ),
                'updates': project.updates.all(),
                'media_items': project.gallery.all(),
                'related_projects': related_projects,
            }
        )
        return context

class ParticipationMethodListView(TemplateView):
    """Lists the different ways people can participate."""

    template_name = 'charity/participation_methods.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['methods'] = ParticipationMethod.objects.filter(is_active=True).order_by(
            'display_order'
        )
        context['impact_stats'] = ImpactStat.objects.filter(is_active=True).order_by(
            'display_order'
        )
        return context

class CompletedProjectListView(ListView):
    """Archive of completed projects with optional year filtering."""

    model = CharityProject
    template_name = 'charity/completed_projects.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        queryset = (
            CharityProject.objects.filter(status=CharityProject.ProjectStatus.COMPLETED)
            .prefetch_related('gallery')
            .order_by('-completion_date', '-updated_at')
        )

        year = self.request.GET.get('year')
        if year and year.isdigit():
            queryset = queryset.filter(completion_date__year=int(year))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        years = CharityProject.objects.filter(
            status=CharityProject.ProjectStatus.COMPLETED, completion_date__isnull=False
        ).dates('completion_date', 'year', order='DESC')
        context['years'] = years
        context['selected_year'] = self.request.GET.get('year', '')
        return context


class DonationSuccess(TemplateView):
    template_name = 'charity/donation_success.html'

