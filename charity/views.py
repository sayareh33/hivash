from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from .models import (
    CharityProject,
    ProjectGallery,
    Donation,
    DonationReceipt,
    PaymentTransaction,
    PaymentStatus
)
from .forms import (
    CharityProjectForm,
    ProjectGalleryForm,
    DonationForm,
    DonationAdminForm,
    DonationReceiptForm,
    PaymentTransactionForm,
    DonationFilterForm
)


class CharityView(TemplateView):
    template_name = 'charity/charity.html'

# ------------------- CharityProject Views -------------------
class ProjectListView(generic.ListView):
    model = CharityProject
    template_name = 'charity/project_list.html'
    context_object_name = 'projects'
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)

        # فیلتر پروژه‌های ویژه
        if self.request.GET.get('featured'):
            queryset = queryset.filter(is_featured=True)

        # جستجو
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(short_description__icontains=search)
            )

        return queryset.order_by('-is_featured', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_projects'] = CharityProject.objects.filter(
            is_featured=True,
            is_active=True
        )[:3]
        return context


class ProjectDetailView(generic.DetailView):
    model = CharityProject
    template_name = 'charity/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()

        # فقط برای کاربران مدیر یا پروژه‌های فعال
        if not project.is_active and not self.request.user.is_staff:
            raise PermissionDenied

        context['donations'] = project.donations.filter(
            payment_status=PaymentStatus.PAID
        ).select_related('donor')[:10]
        context['gallery'] = project.gallery.all()
        context['donation_form'] = DonationForm(
            initial={'project': project.id},
            user=self.request.user
        )
        return context


class ProjectCreateView(PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = CharityProject
    form_class = CharityProjectForm
    template_name = 'charity/project_form.html'
    permission_required = 'charity.add_charityproject'
    success_message = "پروژه جدید با موفقیت ایجاد شد."

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('charity:project_detail', kwargs={'pk': self.object.pk})


class ProjectUpdateView(PermissionRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = CharityProject
    form_class = CharityProjectForm
    template_name = 'charity/project_form.html'
    permission_required = 'charity.change_charityproject'
    success_message = "پروژه با موفقیت به‌روزرسانی شد."

    def get_success_url(self):
        return reverse_lazy('charity:project_detail', kwargs={'pk': self.object.pk})


class ProjectDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = CharityProject
    template_name = 'charity/project_confirm_delete.html'
    success_url = reverse_lazy('charity:project_list')
    permission_required = 'charity.delete_charityproject'

    def delete(self, request, *args, **kwargs):
        from django.contrib import messages
        messages.success(request, "پروژه با موفقیت حذف شد.")
        return super().delete(request, *args, **kwargs)


# ------------------- ProjectGallery Views -------------------
class GalleryCreateView(PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = ProjectGallery
    form_class = ProjectGalleryForm
    template_name = 'charity/gallery_form.html'
    permission_required = 'charity.add_projectgallery'
    success_message = "تصویر جدید با موفقیت به گالری اضافه شد."

    def get_success_url(self):
        return reverse_lazy('charity:project_detail', kwargs={'pk': self.kwargs['project_id']})

    def form_valid(self, form):
        project = get_object_or_404(CharityProject, pk=self.kwargs['project_id'])
        form.instance.project = project
        return super().form_valid(form)


class GalleryDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = ProjectGallery
    template_name = 'charity/gallery_confirm_delete.html'
    permission_required = 'charity.delete_projectgallery'

    def get_success_url(self):
        project_id = self.object.charityproject_set.first().id
        return reverse_lazy('charity:project_detail', kwargs={'pk': project_id})


# ------------------- Donation Views -------------------
class DonationListView(PermissionRequiredMixin, generic.ListView):
    model = Donation
    template_name = 'charity/donation_list.html'
    context_object_name = 'donations'
    paginate_by = 25
    permission_required = 'charity.view_donation'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'donor')
        self.filter_form = DonationFilterForm(self.request.GET)

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data.get('project'):
                queryset = queryset.filter(project=data['project'])
            if data.get('payment_status'):
                queryset = queryset.filter(payment_status=data['payment_status'])
            if data.get('payment_gateway'):
                queryset = queryset.filter(payment_gateway=data['payment_gateway'])
            if data.get('start_date') and data.get('end_date'):
                queryset = queryset.filter(
                    donation_date__date__range=[data['start_date'], data['end_date']]
                )
            if data.get('min_amount'):
                queryset = queryset.filter(amount__gte=data['min_amount'])
            if data.get('max_amount'):
                queryset = queryset.filter(amount__lte=data['max_amount'])

        return queryset.order_by('-donation_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['total_amount'] = self.get_queryset().aggregate(
            total=Sum('amount')
        )['total'] or 0
        return context


class DonationCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = Donation
    form_class = DonationForm
    template_name = 'charity/donation_create.html'
    success_message = "پرداخت شما با موفقیت ثبت شد. لطفا پرداخت را تکمیل کنید."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.donor = self.request.user
        response = super().form_valid(form)

        # در اینجا می‌توانید پرداخت را به درگاه پرداخت ارسال کنید
        # و کاربر را به صفحه پرداخت هدایت کنید

        return response

    def get_success_url(self):
        return reverse_lazy('charity:donation_detail', kwargs={'pk': self.object.pk})


class DonationDetailView(LoginRequiredMixin, generic.DetailView):
    model = Donation
    template_name = 'charity/donation_detail.html'

    def dispatch(self, request, *args, **kwargs):
        # فقط اهداکننده یا مدیران می‌توانند مشاهده کنند
        donation = self.get_object()
        if not (request.user.is_staff or donation.donor == request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class DonationUpdateView(PermissionRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Donation
    form_class = DonationAdminForm
    template_name = 'charity/donation_form.html'
    permission_required = 'charity.change_donation'
    success_message = "اطلاعات اهدا با موفقیت به‌روزرسانی شد."


class UserDonationsView(LoginRequiredMixin, generic.ListView):
    model = Donation
    template_name = 'charity/user_donations.html'
    context_object_name = 'donations'
    paginate_by = 10

    def get_queryset(self):
        return Donation.objects.filter(
            donor=self.request.user
        ).select_related('project').order_by('-donation_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_donated'] = self.get_queryset().filter(
            payment_status=PaymentStatus.PAID
        ).aggregate(total=Sum('amount'))['total'] or 0
        return context


# ------------------- DonationReceipt Views -------------------
class ReceiptCreateView(PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
    model = DonationReceipt
    form_class = DonationReceiptForm
    template_name = 'charity/receipt_form.html'
    permission_required = 'charity.add_donationreceipt'
    success_message = "رسید پرداخت با موفقیت صادر شد."

    def get_initial(self):
        initial = super().get_initial()
        donation_id = self.kwargs.get('donation_id')
        if donation_id:
            initial['donation'] = get_object_or_404(Donation, pk=donation_id)
        return initial

    def get_success_url(self):
        return reverse_lazy('charity:donation_detail', kwargs={'pk': self.object.donation.pk})


class ReceiptDownloadView(LoginRequiredMixin, generic.DetailView):
    model = DonationReceipt
    template_name = 'charity/receipt_download.html'

    def get(self, request, *args, **kwargs):
        receipt = self.get_object()
        if not (request.user.is_staff or receipt.donation.donor == request.user):
            raise PermissionDenied

        # در اینجا می‌توانید فایل PDF را برای دانلود ارسال کنید
        # به عنوان مثال:
        # response = FileResponse(receipt.pdf_file, as_attachment=True)
        # return response

        return super().get(request, *args, **kwargs)


# ------------------- PaymentTransaction Views -------------------
class TransactionListView(PermissionRequiredMixin, generic.ListView):
    model = PaymentTransaction
    template_name = 'charity/transaction_list.html'
    permission_required = 'charity.view_paymenttransaction'
    paginate_by = 25

    def get_queryset(self):
        queryset = super().get_queryset().select_related('donation')
        donation_id = self.request.GET.get('donation_id')
        if donation_id:
            queryset = queryset.filter(donation_id=donation_id)
        return queryset.order_by('-created_at')


class TransactionDetailView(PermissionRequiredMixin, generic.DetailView):
    model = PaymentTransaction
    template_name = 'charity/transaction_detail.html'
    permission_required = 'charity.view_paymenttransaction'


# ------------------- AJAX Views -------------------
class GetProjectDetailsView(generic.View):
    def get(self, request, *args, **kwargs):
        project_id = request.GET.get('project_id')
        project = get_object_or_404(CharityProject, pk=project_id)

        data = {
            'title': project.title,
            'description': project.short_description,
            'progress': project.progress,
            'remaining_days': project.remaining_days,
            'image_url': project.image.url if project.image else '',
        }

        return JsonResponse(data)





# from django.views import generic
# from django.urls import reverse_lazy
# from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
# from django.contrib.messages.views import SuccessMessageMixin
# from django.db.models import Sum
# from .models import CharityProject, ProjectGallery, Donation, DonationReceipt, PaymentTransaction
# from .forms import (
#     CharityProjectForm,
#     ProjectGalleryForm,
#     DonationForm,
#     DonationReceiptForm,
#     PaymentTransactionForm
# )
#
#
# ## ویوهای مربوط به CharityProject ##
#
# class CharityProjectListView(generic.ListView):
#     model = CharityProject
#     template_name = 'charity/project_list.html'
#     context_object_name = 'projects'
#     paginate_by = 10
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         # فیلتر کردن پروژه‌های فعال فقط برای کاربران عادی
#         if not self.request.user.is_staff:
#             queryset = queryset.filter(is_active=True)
#         return queryset
#
#
# class CharityProjectDetailView(generic.DetailView):
#     model = CharityProject
#     template_name = 'charity/project_detail.html'
#     context_object_name = 'project'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         # اضافه کردن تعداد اهداکنندگان و مبلغ جمع‌آوری شده به کانتکست
#         project = self.get_object()
#         context['donations_count'] = project.donors_count
#         context['total_donations'] = project.donations.filter(
#             payment_status='paid'
#         ).aggregate(total=Sum('amount'))['total'] or 0
#         return context
#
#
# class CharityProjectCreateView(PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
#     model = CharityProject
#     form_class = CharityProjectForm
#     template_name = 'charity/project_form.html'
#     permission_required = 'charity.add_charityproject'
#     success_message = "پروژه جدید با موفقیت ایجاد شد."
#
#     def form_valid(self, form):
#         form.instance.created_by = self.request.user
#         return super().form_valid(form)
#
#
# class CharityProjectUpdateView(PermissionRequiredMixin, SuccessMessageMixin, generic.UpdateView):
#     model = CharityProject
#     form_class = CharityProjectForm
#     template_name = 'charity/project_form.html'
#     permission_required = 'charity.change_charityproject'
#     success_message = "پروژه با موفقیت به‌روزرسانی شد."
#
#
# class CharityProjectDeleteView(PermissionRequiredMixin, generic.DeleteView):
#     model = CharityProject
#     template_name = 'charity/project_confirm_delete.html'
#     success_url = reverse_lazy('charity:project_list')
#     permission_required = 'charity.delete_charityproject'
#
#     def delete(self, request, *args, **kwargs):
#         from django.contrib import messages
#         messages.success(request, "پروژه با موفقیت حذف شد.")
#         return super().delete(request, *args, **kwargs)
#
#
# ## ویوهای مربوط به ProjectGallery ##
#
# class ProjectGalleryCreateView(PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
#     model = ProjectGallery
#     form_class = ProjectGalleryForm
#     template_name = 'charity/gallery_form.html'
#     permission_required = 'charity.add_projectgallery'
#     success_message = "تصویر جدید با موفقیت به گالری اضافه شد."
#
#     def get_success_url(self):
#         return reverse_lazy('charity:project_detail', kwargs={'pk': self.kwargs['project_id']})
#
#
# class ProjectGalleryDeleteView(PermissionRequiredMixin, generic.DeleteView):
#     model = ProjectGallery
#     template_name = 'charity/gallery_confirm_delete.html'
#     permission_required = 'charity.delete_projectgallery'
#
#     def get_success_url(self):
#         project_id = self.object.charityproject_set.first().id
#         return reverse_lazy('charity:project_detail', kwargs={'pk': project_id})
#
#
# ## ویوهای مربوط به Donation ##
#
# class DonationListView(PermissionRequiredMixin, generic.ListView):
#     model = Donation
#     template_name = 'charity/donation_list.html'
#     context_object_name = 'donations'
#     paginate_by = 20
#     permission_required = 'charity.view_donation'
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         # فیلتر بر اساس پروژه اگر پارامتر ارسال شده باشد
#         project_id = self.request.GET.get('project_id')
#         if project_id:
#             queryset = queryset.filter(project_id=project_id)
#         return queryset.select_related('project', 'donor')
#
#
# class DonationDetailView(PermissionRequiredMixin, generic.DetailView):
#     model = Donation
#     template_name = 'charity/donation_detail.html'
#     context_object_name = 'donation'
#     permission_required = 'charity.view_donation'
#
#
# class DonationUpdateView(PermissionRequiredMixin, SuccessMessageMixin, generic.UpdateView):
#     model = Donation
#     form_class = DonationForm
#     template_name = 'charity/donation_form.html'
#     permission_required = 'charity.change_donation'
#     success_message = "اطلاعات اهدا با موفقیت به‌روزرسانی شد."
#
#
# class UserDonationListView(LoginRequiredMixin, generic.ListView):
#     model = Donation
#     template_name = 'charity/user_donation_list.html'
#     context_object_name = 'donations'
#     paginate_by = 10
#
#     def get_queryset(self):
#         return Donation.objects.filter(
#             donor=self.request.user
#         ).select_related('project').order_by('-donation_date')
#
#
# class DonationCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.CreateView):
#     model = Donation
#     form_class = DonationForm
#     template_name = 'charity/donation_create.html'
#     success_message = "پرداخت شما با موفقیت ثبت شد. لطفا پرداخت را تکمیل کنید."
#
#     def get_initial(self):
#         initial = super().get_initial()
#         if 'project_id' in self.kwargs:
#             initial['project'] = self.kwargs['project_id']
#         return initial
#
#     def form_valid(self, form):
#         form.instance.donor = self.request.user
#         return super().form_valid(form)
#
#     def get_success_url(self):
#         return reverse_lazy('payment:process', kwargs={'donation_id': self.object.id})
#
#
# ## ویوهای مربوط به DonationReceipt ##
#
# class DonationReceiptCreateView(PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
#     model = DonationReceipt
#     form_class = DonationReceiptForm
#     template_name = 'charity/receipt_form.html'
#     permission_required = 'charity.add_donationreceipt'
#     success_message = "رسید پرداخت با موفقیت صادر شد."
#
#     def get_success_url(self):
#         return reverse_lazy('charity:donation_detail', kwargs={'pk': self.object.donation.id})
#
#
# class DonationReceiptDownloadView(LoginRequiredMixin, generic.DetailView):
#     model = DonationReceipt
#     template_name = 'charity/receipt_download.html'
#
#     def get(self, request, *args, **kwargs):
#         receipt = self.get_object()
#         # بررسی اینکه کاربر مجاز به دیدن رسید است
#         if request.user.is_staff or receipt.donation.donor == request.user:
#             # در اینجا می‌توانید فایل PDF را برای دانلود ارسال کنید
#             pass
#         return super().get(request, *args, **kwargs)
#
#
# ## ویوهای مربوط به PaymentTransaction ##
#
# class PaymentTransactionListView(PermissionRequiredMixin, generic.ListView):
#     model = PaymentTransaction
#     template_name = 'charity/transaction_list.html'
#     context_object_name = 'transactions'
#     paginate_by = 20
#     permission_required = 'charity.view_paymenttransaction'
#
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         # فیلتر بر اساس donation اگر پارامتر ارسال شده باشد
#         donation_id = self.request.GET.get('donation_id')
#         if donation_id:
#             queryset = queryset.filter(donation_id=donation_id)
#         return queryset.select_related('donation')
#
#
# class PaymentTransactionDetailView(PermissionRequiredMixin, generic.DetailView):
#     model = PaymentTransaction
#     template_name = 'charity/transaction_detail.html'
#     context_object_name = 'transaction'
#     permission_required = 'charity.view_paymenttransaction'
#
#
# class PaymentTransactionUpdateView(PermissionRequiredMixin, SuccessMessageMixin, generic.UpdateView):
#     model = PaymentTransaction
#     form_class = PaymentTransactionForm
#     template_name = 'charity/transaction_form.html'
#     permission_required = 'charity.change_paymenttransaction'
#     success_message = "تراکنش با موفقیت به‌روزرسانی شد."
#





# # charity/views.py
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_optional
# from .models import CharityProject, Donation
#
#
# @login_optional
# def charity_home(request):
#     projects = CharityProject.objects.filter(is_active=True)
#     stats = {
#         'total_donations': Donation.objects.total_amount(),
#         'completed_projects': CharityProject.objects.completed().count(),
#         # سایر آمارها
#     }
#     return render(request, 'charity/index.html', {
#         'projects': projects,
#         'stats': stats
#     })
#
#
# def donate(request):
#     if request.method == 'POST':
#         # پردازش فرم پرداخت
#         return redirect('donation_success')
#     return render(request, 'charity/donate.html')
#
#
# from django.shortcuts import render
#
# # Create your views here.
