from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/update/', views.product_update, name='product_update'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('<int:product_pk>/quality/add/', views.quality_create, name='quality_create'),
    path('quality/<int:pk>/update/', views.quality_update, name='quality_update'),
    path('quality/<int:pk>/delete/', views.quality_delete, name='quality_delete'),
    path('price-list/upload/', views.price_list_upload, name='price_list_upload'),
    path('price-list/template/download/', views.download_price_list_template, name='download_price_list_template'),
    path('search/', views.product_search_api, name='product_search_api'),
]
