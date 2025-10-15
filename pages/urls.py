from django.urls import path

from . import views
from .views import HomePageView, AboutUsView

app_name = 'pages'
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('aboutus/', AboutUsView.as_view(), name='aboutus'),
    # path('contactus/', ContactUsView.as_view(), name='contactus'),
    path('contactus/', views.contactus_view, name='contactus'),
]