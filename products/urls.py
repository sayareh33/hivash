from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('foods/', views.FoodsListView.as_view(), name='foods_list'),
    path('bags/', views.BagsListView.as_view(), name='bags_list'),
    path('category/<slug:slug>/', views.CategoryProductListView.as_view(), name='category_products'),
    path('discounts/', views.DiscountedProductsView.as_view(), name='discounted_products'),

    path('<int:product_id>/comment/', views.CommentCreateView.as_view(), name='add_comment'),

    path('search/', views.ProductSearchView.as_view(), name='product_search'),
    path('search/advanced/', views.AdvancedSearchView.as_view(), name='advanced_search'),
    path('search/unified/', views.UnifiedSearchView.as_view(), name='unified_search'),

    path('wishlist/', views.wishlist_view, name='wishlist'),
    # path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    # path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),

    # ویوهای AJAX (جدید)
    path('wishlist/ajax/add/', views.add_to_wishlist_ajax, name='add_to_wishlist_ajax'),
    path('wishlist/ajax/remove/', views.remove_from_wishlist_ajax, name='remove_from_wishlist_ajax'),

    # Keep product detail fallback last so it does not shadow other routes.
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]
