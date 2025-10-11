from django.urls import path

from .views import (
    CharityHomeView,
    ProjectListView,
    ProjectDetailView,
    CompletedProjectListView,
    ParticipationMethodListView, DonationSuccess,
)

app_name = 'charity'

urlpatterns = [
    path('', CharityHomeView.as_view(), name='home'),
    path('projects/', ProjectListView.as_view(), name='project_list'),
    path('projects/completed/', CompletedProjectListView.as_view(), name='completed_projects'),
    path('projects/<slug:slug>/', ProjectDetailView.as_view(), name='project_detail'),
    path('participation/', ParticipationMethodListView.as_view(), name='participation_methods'),
    path('success/', DonationSuccess.as_view(), name='success')
]
