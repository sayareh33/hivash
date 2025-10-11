
from django.urls import path
from . import views

app_name = 'carts'

urlpatterns = [
    path('', views.cart_detail_view, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('ajax-add/<int:product_id>/', views.ajax_add_to_cart, name='ajax_add_to_cart'),
    path('ajax-remove/<int:product_id>/', views.ajax_remove_from_cart, name='ajax_remove_from_cart'),
    path('ajax-update/<int:product_id>/', views.ajax_update_cart_item, name='ajax_update_cart_item'),
    path('ajax-clear/', views.ajax_clear_cart, name='ajax_clear_cart'),
    path('ajax-shipping/', views.ajax_update_shipping, name='ajax_update_shipping'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
]
