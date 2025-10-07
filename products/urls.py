from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('foods/', views.FoodsListView.as_view(), name='foods_list'),
    path('bags/', views.BagsListView.as_view(), name='bags_list'),
    # جزئیات محصول
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('category/<slug:slug>/', views.CategoryProductListView.as_view(), name='category_products'),
    path('discounts/', views.DiscountedProductsView.as_view(), name='discounted_products'),

    # ایجاد نظر
    path('<int:product_id>/comment/', views.CommentCreateView.as_view(), name='add_comment'),

    # جستجوی ساده
    path('search/', views.ProductSearchView.as_view(), name='product_search'),

    # جستجوی پیشرفته
    path('search/advanced/', views.AdvancedSearchView.as_view(), name='advanced_search'),

    # جستجوی unified (محصول + مقاله)
    path('search/unified/', views.UnifiedSearchView.as_view(), name='unified_search'),

    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
]
