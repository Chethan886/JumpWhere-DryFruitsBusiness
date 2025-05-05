"""
URL Configuration for dry_fruits_project
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('customers/', include('customers.urls')),
    path('products/', include('products.urls')),
    path('billing/', include('billing.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
