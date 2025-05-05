from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='billing_list'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('products/', views.product_selection, name='product_selection'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/view/', views.view_cart, name='view_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/issue/', views.invoice_issue, name='invoice_issue'),
    path('invoices/<int:pk>/cancel/', views.invoice_cancel, name='invoice_cancel'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/mark-paid/', views.invoice_mark_paid, name='invoice_mark_paid'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:invoice_pk>/items/add/', views.invoice_item_add, name='invoice_item_add'),
    path('invoice-items/<int:pk>/edit/', views.invoice_item_edit, name='invoice_item_edit'),
    path('invoice-items/<int:pk>/delete/', views.invoice_item_delete, name='invoice_item_delete'),
    path('api/customers/search/', views.customer_search_api, name='customer_search_api'),
    path('api/products/search/', views.product_search_api, name='product_search_api'),
    path('api/product-quality/price/', views.product_quality_price_api, name='product_quality_price_api'),
]
