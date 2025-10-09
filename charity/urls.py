from django.urls import path
from . import views

app_name = 'charity'

urlpatterns = [
    path('charity/', views.CharityView.as_view(), name='charity'),
    # پروژه‌های خیریه
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/add/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

    # گالری پروژه‌ها
    path('projects/<int:project_id>/gallery/add/', views.GalleryCreateView.as_view(), name='gallery_add'),
    path('gallery/<int:pk>/delete/', views.GalleryDeleteView.as_view(), name='gallery_delete'),

    # اهداها
    path('donations/', views.DonationListView.as_view(), name='donation_list'),
    path('donations/add/', views.DonationCreateView.as_view(), name='donation_create'),
    path('donations/<int:pk>/', views.DonationDetailView.as_view(), name='donation_detail'),
    path('donations/<int:pk>/edit/', views.DonationUpdateView.as_view(), name='donation_update'),
    path('my-donations/', views.UserDonationsView.as_view(), name='user_donations'),

    # رسیدهای پرداخت
    path('donations/<int:donation_id>/receipt/', views.ReceiptCreateView.as_view(), name='receipt_create'),
    path('receipts/<int:pk>/download/', views.ReceiptDownloadView.as_view(), name='receipt_download'),

    # تراکنش‌ها
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),

    # AJAX
    path('ajax/get-project-details/', views.GetProjectDetailsView.as_view(), name='ajax_project_details'),
]