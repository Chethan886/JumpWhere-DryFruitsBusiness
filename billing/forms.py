from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import Invoice, InvoiceItem
from customers.models import Customer
from products.models import Product, ProductQuality

class InvoiceForm(forms.ModelForm):
    """Form for creating and updating invoices."""
    customer_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search customer...', 'readonly': True})
    )
    customer_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number...', 'readonly': True})
    )
    
    class Meta:
        model = Invoice
        fields = ['payment_type', 'discount_percentage', 'tax_percentage', 'payment_due_date', 'notes']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'payment_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['discount_percentage'].initial = 0
        self.fields['tax_percentage'].initial = 0
        
        # If we're editing an existing invoice, populate the customer fields
        if self.instance.pk:
            self.fields['customer_id'].initial = self.instance.customer.id
            self.fields['customer_name'].initial = self.instance.customer.name
            self.fields['customer_phone'].initial = self.instance.customer.phone

class InvoiceItemForm(forms.ModelForm):
    """Form for creating and updating invoice items."""
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    product_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search product...', 'readonly': True}),
        required=False
    )
    
    class Meta:
        model = InvoiceItem
        fields = ['product_quality', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'product_quality': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'min': '0.001'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }
    
    def __init__(self, *args, **kwargs):
        product_id = kwargs.pop('product_id', None)
        super().__init__(*args, **kwargs)
        
        if product_id:
            self.fields['product_id'].initial = product_id
            try:
                product = Product.objects.get(id=product_id)
                self.fields['product_name'].initial = product.name
                
                # Populate the product_quality choices
                qualities = ProductQuality.objects.filter(product_id=product_id)
                if qualities.exists():
                    self.fields['product_quality'].queryset = qualities
                    # If we're editing an existing item, don't override the selected quality
                    if not self.instance.pk:
                        self.fields['product_quality'].initial = qualities.first().id
                else:
                    self.fields['product_quality'].queryset = ProductQuality.objects.none()
                    self.fields['product_quality'].help_text = "No quality variants available for this product"
            except Product.DoesNotExist:
                self.fields['product_quality'].queryset = ProductQuality.objects.none()
        else:
            self.fields['product_quality'].queryset = ProductQuality.objects.none()
        
        # Set initial discount percentage
        if not self.instance.pk:
            self.fields['discount_percentage'].initial = 0

class CustomerSearchForm(forms.Form):
    """Form for searching customers."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name or phone...'})
    )

class ProductSearchForm(forms.Form):
    """Form for searching products."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search products...'})
    )

class InvoiceSearchForm(forms.Form):
    """Form for searching and filtering invoices."""
    STATUS_CHOICES = (
        ('', 'All Statuses'),
    ) + Invoice.STATUS_CHOICES
    
    PAYMENT_TYPE_CHOICES = (
        ('', 'All Payment Types'),
    ) + Invoice.PAYMENT_TYPE_CHOICES
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by invoice # or customer...'})
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    payment_type = forms.ChoiceField(
        choices=PAYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date range to last 30 days
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        self.fields['date_from'].initial = thirty_days_ago
        self.fields['date_to'].initial = today
