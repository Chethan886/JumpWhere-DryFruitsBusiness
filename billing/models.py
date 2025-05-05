from django.db import models
from django.core.validators import MinValueValidator
from authentication.models import User
from customers.models import Customer
from products.models import Product, ProductQuality

class Invoice(models.Model):
    """Model for storing invoice information."""
    PAYMENT_TYPE_CHOICES = (
        ('cash', 'Cash'),
        ('upi', 'UPI/Card'),
        ('credit', 'Credit'),
    )
    
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_payment', 'Pending Payment'),
        ('issued', 'Issued'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    invoice_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='invoices')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    due_date = models.DateField(null=True, blank=True)
    payment_due_date = models.DateField(null=True, blank=True, help_text="Expected date of payment")
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.customer.name}"
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def amount_due(self):
        """Calculate the amount due."""
        return self.total - self.amount_paid
    
    @property
    def is_paid(self):
        """Check if the invoice is fully paid."""
        return self.amount_paid >= self.total
    
    @property
    def is_overdue(self):
        """Check if the invoice is overdue."""
        from django.utils import timezone
        return self.due_date and self.due_date &lt; timezone.now().date() and not self.is_paid

class InvoiceItem(models.Model):
    """Model for storing invoice item information."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_quality = models.ForeignKey(ProductQuality, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.product.name} - {self.product_quality.get_quality_display()} ({self.quantity} kg)"
    
    class Meta:
        ordering = ['id']
