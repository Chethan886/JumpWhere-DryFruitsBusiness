from django import forms
from .models import Product, ProductQuality, PriceList

class ProductForm(forms.ModelForm):
    """Form for creating and updating products."""
    class Meta:
        model = Product
        fields = ['name', 'description', 'image_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'image_url': forms.URLInput(attrs={'placeholder': 'https://example.com/image.jpg'})
        }

class ProductQualityForm(forms.ModelForm):
    """Form for creating and updating product quality variants."""
    class Meta:
        model = ProductQuality
        fields = ['quality', 'retail_price', 'wholesale_price', 'broker_price', 'stock_quantity']
        widgets = {
            'retail_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'wholesale_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'broker_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})
        }

class PriceListUploadForm(forms.ModelForm):
    """Form for uploading price lists."""
    class Meta:
        model = PriceList
        fields = ['file']

class ProductSearchForm(forms.Form):
    """Form for searching products."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products...'
        })
    )
