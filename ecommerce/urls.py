# ecommerce/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ecommerce_view, {'page_type': 'home'}, name='home'),  # Homepage view
    path('product/<slug:product_slug>/', views.ecommerce_view, {'page_type': 'product_detail'}, name='product_detail'),  # Product detail page
    path('add_to_cart/<slug:product_slug>/', views.ecommerce_view, {'page_type': 'add_to_cart'}, name='add_to_cart'),  # Add to cart
    path('cart/', views.ecommerce_view, {'page_type': 'view_cart'}, name='view_cart'),  # View cart page
    path('gym-equipment/', views.equipment, name='equipment'),  # Equipment page
    path('apparel/', views.apparel, name='apparel'),  # Apparel page
    path('supplements/', views.supplements, name='supplements'),  # Supplements page
    path('contact/', views.contact, name='contact'),
    path('update_cart/', views.update_cart, name='update_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    # path('process_checkout/', views.process_checkout, name='process_checkout'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('order_confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('admin/confirm_cod/<int:order_id>/', views.confirm_cod_payment, name='confirm_cod_payment'),
    path('admin/mark_shipped/<int:order_id>/', views.mark_order_shipped, name='mark_order_shipped'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.user_register, name='user_register'),
    path('blockchain_admin/', views.blockchain_admin, name='blockchain_admin'),
]
