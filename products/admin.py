from django.contrib import admin
from .models import Product, ProductQuality, PriceList

class ProductQualityInline(admin.TabularInline):
    model = ProductQuality
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    inlines = [ProductQualityInline]

@admin.register(ProductQuality)
class ProductQualityAdmin(admin.ModelAdmin):
    list_display = ('product', 'quality', 'retail_price', 'wholesale_price', 'broker_price', 'stock_quantity')
    list_filter = ('quality',)
    search_fields = ('product__name',)

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_by', 'uploaded_at', 'processed')
    list_filter = ('processed',)
    readonly_fields = ('uploaded_at',)
