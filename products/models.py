from django.db import models
from django.db.models import Sum
from django.utils import timezone

class Product(models.Model):
    """Model for storing product information."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="URL to product image")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class ProductQuality(models.Model):
    """Model for storing product quality variants."""
    QUALITY_CHOICES = (
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('economy', 'Economy'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='qualities')
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2)
    broker_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.get_quality_display()}"
    
    class Meta:
        unique_together = ('product', 'quality')
        verbose_name_plural = 'Product Qualities'

class PriceList(models.Model):
    """Model for storing uploaded price lists."""
    file = models.FileField(upload_to='price_lists/')
    uploaded_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Price List #{self.id} ({self.uploaded_at.strftime('%Y-%m-%d')})"
    
    class Meta:
        ordering = ['-uploaded_at']
