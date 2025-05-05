from django.contrib import admin
from .models import Invoice, InvoiceItem

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'created_at', 'payment_type', 'status', 'total', 'amount_paid')
    list_filter = ('status', 'payment_type', 'created_at')
    search_fields = ('invoice_number', 'customer__name', 'customer__phone')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [InvoiceItemInline]

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'product_quality', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('invoice__status',)
    search_fields = ('invoice__invoice_number', 'product__name')
