import uuid
import logging
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from authentication.decorators import executive_required
from customers.models import Customer
from products.models import Product, ProductQuality
from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemForm, CustomerSearchForm, ProductSearchForm, InvoiceSearchForm
from .utils import generate_invoice_pdf
from django.db import models

# Set up logger
logger = logging.getLogger(__name__)

@login_required
@executive_required
def invoice_list(request):
    """View for listing all invoices."""
    form = InvoiceSearchForm(request.GET)
    invoices = Invoice.objects.all()
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        status = form.cleaned_data.get('status')
        payment_type = form.cleaned_data.get('payment_type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if query:
            invoices = invoices.filter(
                Q(invoice_number__icontains=query) | 
                Q(customer__name__icontains=query) |
                Q(customer__phone__icontains=query)
            )
        
        if status:
            invoices = invoices.filter(status=status)
        
        if payment_type:
            invoices = invoices.filter(payment_type=payment_type)
        
        if date_from:
            invoices = invoices.filter(created_at__date__gte=date_from)
        
        if date_to:
            invoices = invoices.filter(created_at__date__lte=date_to)
    
    # Get summary statistics
    total_amount = invoices.aggregate(total=Sum('total'))['total'] or 0
    paid_amount = invoices.aggregate(paid=Sum('amount_paid'))['paid'] or 0
    pending_amount = total_amount - paid_amount
    
    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices,
        'form': form,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'pending_amount': pending_amount,
    })

@login_required
@executive_required
def product_selection(request):
    """View for selecting products to add to cart."""
    # Clear cart if starting a new bill
    if request.GET.get('clear_cart') == 'true':
        if 'cart' in request.session:
            del request.session['cart']
            request.session.modified = True
    
    # Initialize cart if it doesn't exist
    if 'cart' not in request.session:
        request.session['cart'] = []
    
    # Get all products with their qualities
    products = Product.objects.all().prefetch_related('qualities')
    
    # Search functionality
    query = request.GET.get('query', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Get cart count
    cart_count = len(request.session.get('cart', []))
    
    return render(request, 'billing/product_selection.html', {
        'products': products,
        'query': query,
        'cart_count': cart_count,
    })

@login_required
@executive_required
def add_to_cart(request):
    """AJAX view for adding a product to cart."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = int(data.get('product_id'))
            quality_id = int(data.get('quality_id'))
            quantity = float(data.get('quantity', 1))
            unit = data.get('unit', 'kg')
            
            # Convert to kg if needed
            if unit == 'g':
                quantity = quantity / 1000
            
            # Get product and quality
            product = Product.objects.get(id=product_id)
            quality = ProductQuality.objects.get(id=quality_id)
            
            # Get price based on customer type (default to retail)
            # Convert to string first to ensure proper serialization in session
            price = str(quality.retail_price)
            
            # Initialize cart if it doesn't exist
            if 'cart' not in request.session:
                request.session['cart'] = []
            
            # Check if item already exists in cart
            cart = request.session['cart']
            item_exists = False
            
            for i, item in enumerate(cart):
                if item['product_id'] == product_id and item['quality_id'] == quality_id:
                    # Update quantity
                    cart[i]['quantity'] = float(cart[i]['quantity']) + quantity
                    cart[i]['subtotal'] = str(Decimal(cart[i]['price']) * Decimal(str(cart[i]['quantity'])))
                    item_exists = True
                    break
            
            if not item_exists:
                # Add new item to cart
                cart.append({
                    'product_id': product_id,
                    'product_name': product.name,
                    'quality_id': quality_id,
                    'quality_name': quality.get_quality_display(),
                    'quantity': str(quantity),
                    'unit': 'kg',  # Always store as kg
                    'price': price,
                    'subtotal': str(Decimal(price) * Decimal(str(quantity))),
                    'image_url': product.image_url if hasattr(product, 'image_url') else None,
                })
            
            request.session['cart'] = cart
            request.session.modified = True
            
            return JsonResponse({
                'success': True, 
                'message': f'{product.name} - {quality.get_quality_display()} added to cart',
                'cart_count': len(cart)
            })
            
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@executive_required
def view_cart(request):
    """View for displaying the cart."""
    cart = request.session.get('cart', [])
    
    # Calculate totals
    subtotal = Decimal('0.00')
    for item in cart:
        subtotal += Decimal(item['subtotal'])
    
    return render(request, 'billing/view_cart.html', {
        'cart': cart,
        'subtotal': subtotal,
    })

@login_required
@executive_required
def update_cart(request):
    """AJAX view for updating cart items."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            index = int(data.get('index'))
            quantity = float(data.get('quantity'))
            unit = data.get('unit', 'kg')
            
            # Convert to kg if needed
            if unit == 'g':
                quantity = quantity / 1000
            
            cart = request.session.get('cart', [])
            
            if 0 <= index < len(cart):
                cart[index]['quantity'] = str(quantity)
                cart[index]['subtotal'] = str(Decimal(cart[index]['price']) * Decimal(str(quantity)))
                
                request.session['cart'] = cart
                request.session.modified = True
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Cart updated',
                    'subtotal': cart[index]['subtotal']
                })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid item index'}, status=400)
            
        except Exception as e:
            logger.error(f"Error updating cart: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@executive_required
def remove_from_cart(request):
    """AJAX view for removing an item from cart."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            index = int(data.get('index'))
            
            cart = request.session.get('cart', [])
            
            if 0 <= index < len(cart):
                removed_item = cart.pop(index)
                
                request.session['cart'] = cart
                request.session.modified = True
                
                return JsonResponse({
                    'success': True, 
                    'message': f'{removed_item["product_name"]} removed from cart',
                    'cart_count': len(cart)
                })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid item index'}, status=400)
            
        except Exception as e:
            logger.error(f"Error removing from cart: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@executive_required
def checkout(request):
    """View for checkout process."""
    cart = request.session.get('cart', [])
    
    if not cart:
        messages.warning(request, 'Your cart is empty. Please add products before checkout.')
        return redirect('product_selection')
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            customer_id = form.cleaned_data.get('customer_id')
            
            if not customer_id:
                messages.error(request, 'Please select a customer.')
                return render(request, 'billing/checkout.html', {'form': form, 'cart': cart})
            
            customer = get_object_or_404(Customer, id=customer_id)
            
            # Generate a unique invoice number
            invoice_number = f"INV-{uuid.uuid4().hex[:8].upper()}"
            
            # Create the invoice
            invoice = form.save(commit=False)
            invoice.invoice_number = invoice_number
            invoice.customer = customer
            invoice.created_by = request.user
            
            # Calculate totals
            subtotal = Decimal('0.00')
            for item in cart:
                subtotal += Decimal(item['subtotal'])
            
            discount_amount = subtotal * (Decimal(str(invoice.discount_percentage)) / Decimal('100'))
            tax_amount = (subtotal - discount_amount) * (Decimal(str(invoice.tax_percentage)) / Decimal('100'))
            total = subtotal - discount_amount + tax_amount
            
            invoice.subtotal = subtotal
            invoice.discount_amount = discount_amount
            invoice.tax_amount = tax_amount
            invoice.total = total
            invoice.save()
            
            # Create invoice items
            for item in cart:
                product = Product.objects.get(id=item['product_id'])
                quality = ProductQuality.objects.get(id=item['quality_id'])
                
                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=product,
                    product_quality=quality,
                    quantity=Decimal(item['quantity']),
                    unit_price=Decimal(item['price']),
                    discount_percentage=Decimal('0'),  # Individual item discounts not implemented in cart
                    discount_amount=Decimal('0'),
                    subtotal=Decimal(item['subtotal'])
                )
            
            # Clear the cart
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
            
            messages.success(request, 'Bill created successfully!')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
    
    # Calculate totals
    subtotal = Decimal('0.00')
    for item in cart:
        subtotal += Decimal(item['subtotal'])
    
    return render(request, 'billing/checkout.html', {
        'form': form,
        'cart': cart,
        'subtotal': subtotal,
    })

@login_required
@executive_required
def invoice_create(request):
    """Redirect to product selection to start the bill creation process."""
    return redirect('product_selection')

@login_required
@executive_required
def invoice_edit(request, pk):
    """View for editing an invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status != 'draft':
        messages.warning(request, 'This invoice has already been issued and cannot be edited.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Invoice updated successfully.')
            return redirect('invoice_edit', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
    
    items = invoice.items.all()
    product_form = ProductSearchForm()
    
    # Calculate totals
    subtotal = sum(item.subtotal for item in items)
    discount_amount = subtotal * (invoice.discount_percentage / 100)
    tax_amount = (subtotal - discount_amount) * (invoice.tax_percentage / 100)
    total = subtotal - discount_amount + tax_amount
    
    return render(request, 'billing/invoice_edit.html', {
        'form': form,
        'invoice': invoice,
        'items': items,
        'product_form': product_form,
        'subtotal': subtotal,
        'discount_amount': discount_amount,
        'tax_amount': tax_amount,
        'total': total,
    })

@login_required
@executive_required
def invoice_detail(request, pk):
    """View for displaying invoice details."""
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    
    # Get all invoices for this customer
    customer_invoices = Invoice.objects.filter(customer=invoice.customer).order_by('-created_at')
    
    # Pass these invoices to the template as customer_payments
    customer_payments = customer_invoices
    
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice,
        'items': items,
        'customer_payments': customer_payments,
    })

@login_required
@executive_required
def invoice_issue(request, pk):
    """View for issuing an invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status != 'draft':
        messages.warning(request, 'This invoice has already been issued.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if not invoice.items.exists():
        messages.error(request, 'Cannot issue an invoice with no items.')
        return redirect('invoice_edit', pk=invoice.pk)
    
    # Calculate totals
    items = invoice.items.all()
    subtotal = sum(item.subtotal for item in items)
    discount_amount = subtotal * (invoice.discount_percentage / 100)
    tax_amount = (subtotal - discount_amount) * (invoice.tax_percentage / 100)
    total = subtotal - discount_amount + tax_amount
    
    # Update invoice
    invoice.subtotal = subtotal
    invoice.discount_amount = discount_amount
    invoice.tax_amount = tax_amount
    invoice.total = total
    
    # Set due date for credit invoices
    if invoice.payment_type == 'credit':
        if not invoice.due_date:
            invoice.due_date = timezone.now().date() + timedelta(days=30)
    
    # Set status to pending_payment instead of paid
    invoice.status = 'pending_payment'
    
    invoice.save()
    
    messages.success(request, 'Invoice issued successfully with pending payment status.')
    return redirect('invoice_detail', pk=invoice.pk)

# Add a new view to mark an invoice as paid
@login_required
@executive_required
def invoice_mark_paid(request, pk):
    """View for marking an invoice as paid."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'paid':
        messages.warning(request, 'This invoice is already marked as paid.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        invoice.status = 'paid'
        invoice.amount_paid = invoice.total
        invoice.save()
        messages.success(request, 'Invoice marked as paid successfully.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    return render(request, 'billing/invoice_confirm_paid.html', {
        'invoice': invoice,
    })

@login_required
@executive_required
def invoice_cancel(request, pk):
    """View for cancelling an invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'cancelled':
        messages.warning(request, 'This invoice is already cancelled.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        invoice.status = 'cancelled'
        invoice.save()
        messages.success(request, 'Invoice cancelled successfully.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    return render(request, 'billing/invoice_confirm_cancel.html', {
        'invoice': invoice,
    })

@login_required
@executive_required
def invoice_delete(request, pk):
    """View for deleting an invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully.')
        return redirect('invoice_list')
    
    return render(request, 'billing/invoice_confirm_delete.html', {
        'invoice': invoice,
    })

@login_required
@executive_required
def invoice_pdf(request, pk):
    """View for generating a PDF of the invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    
    # Generate PDF
    pdf = generate_invoice_pdf(invoice, items)
    
    # Create HTTP response with PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    return response

@login_required
@executive_required
def invoice_item_add(request, invoice_pk):
    """View for adding an item to an invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    
    if invoice.status != 'draft':
        messages.warning(request, 'This invoice has already been issued and cannot be modified.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    # Get product_id from URL parameter
    product_id = request.GET.get('product_id')
    product = None
    
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            # Check if product has any qualities
            if not product.qualities.exists():
                messages.warning(request, f'The product "{product.name}" has no quality variants defined. Please add quality variants first.')
                return redirect('invoice_edit', pk=invoice.pk)
        except Product.DoesNotExist:
            messages.error(request, 'Selected product not found.')
            return redirect('invoice_edit', pk=invoice.pk)
    
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST, product_id=product_id)
        if form.is_valid():
            product_id = form.cleaned_data.get('product_id')
            product = get_object_or_404(Product, id=product_id)
            product_quality = form.cleaned_data.get('product_quality')
            quantity = form.cleaned_data.get('quantity')
            unit_price = form.cleaned_data.get('unit_price')
            discount_percentage = form.cleaned_data.get('discount_percentage')
            
            # Calculate subtotal
            discount_amount = unit_price * quantity * (discount_percentage / 100)
            subtotal = unit_price * quantity - discount_amount
            
            # Create invoice item
            item = form.save(commit=False)
            item.invoice = invoice
            item.product = product
            item.discount_amount = discount_amount
            item.subtotal = subtotal
            item.save()
            
            messages.success(request, 'Item added to invoice successfully.')
            return redirect('invoice_edit', pk=invoice.pk)
    else:
        # Initialize form with product_id if available
        if product:
            # Pass product_id to the form to properly populate product_quality choices
            form = InvoiceItemForm(product_id=product.id, initial={'product_id': product.id, 'product_name': product.name})
        else:
            form = InvoiceItemForm()
    
    return render(request, 'billing/invoice_item_form.html', {
        'form': form,
        'invoice': invoice,
        'title': 'Add Item to Invoice',
        'product': product,  # Pass the product to the template
    })

@login_required
@executive_required
def invoice_item_edit(request, pk):
    """View for editing an invoice item."""
    item = get_object_or_404(InvoiceItem, pk=pk)
    invoice = item.invoice
    product = item.product
    
    if invoice.status != 'draft':
        messages.warning(request, 'This invoice has already been issued and cannot be modified.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        form = InvoiceItemForm(request.POST, instance=item, product_id=item.product.id)
        if form.is_valid():
            quantity = form.cleaned_data.get('quantity')
            unit_price = form.cleaned_data.get('unit_price')
            discount_percentage = form.cleaned_data.get('discount_percentage')
            
            # Calculate subtotal
            discount_amount = unit_price * quantity * (discount_percentage / 100)
            subtotal = unit_price * quantity - discount_amount
            
            # Update invoice item
            item = form.save(commit=False)
            item.discount_amount = discount_amount
            item.subtotal = subtotal
            item.save()
            
            messages.success(request, 'Invoice item updated successfully.')
            return redirect('invoice_edit', pk=invoice.pk)
    else:
        # Initialize form with the existing item data
        initial_data = {
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_quality': item.product_quality.id,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'discount_percentage': item.discount_percentage
        }
        form = InvoiceItemForm(instance=item, product_id=item.product.id, initial=initial_data)
    
    return render(request, 'billing/invoice_item_form.html', {
        'form': form,
        'invoice': invoice,
        'item': item,
        'title': 'Edit Invoice Item',
        'product': product,  # Pass the product to the template
    })

@login_required
@executive_required
def invoice_item_delete(request, pk):
    """View for deleting an invoice item."""
    item = get_object_or_404(InvoiceItem, pk=pk)
    invoice = item.invoice
    
    if invoice.status != 'draft':
        messages.warning(request, 'This invoice has already been issued and cannot be modified.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Invoice item deleted successfully.')
        return redirect('invoice_edit', pk=invoice.pk)
    
    return render(request, 'billing/invoice_item_confirm_delete.html', {
        'item': item,
        'invoice': invoice,
    })

@login_required
@executive_required
def customer_search_api(request):
    """API view for searching customers."""
    query = request.GET.get('q', '')
    logger.info(f"Customer search query: {query}")
    
    if not query or len(query) < 2:
        logger.warning("Search query too short or empty")
        return JsonResponse({'customers': [], 'message': 'Please enter at least 2 characters to search'})
    
    try:
        # Search by name or phone
        customers = Customer.objects.filter(
            Q(name__icontains=query) | Q(phone__icontains=query)
        )[:10]
        
        logger.info(f"Found {customers.count()} customers matching '{query}'")
        
        customer_list = []
        for customer in customers:
            customer_list.append({
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'customer_type': customer.get_customer_type_display(),
                'credit_limit': float(customer.credit_limit),
                'pending_amount': float(customer.total_pending_amount),
            })
        
        return JsonResponse({'customers': customer_list})
    except Exception as e:
        logger.error(f"Error in customer search: {str(e)}")
        return JsonResponse({'customers': [], 'message': f'Error: {str(e)}'}, status=500)

@login_required
@executive_required
def product_quality_price_api(request):
    """API view for getting product quality prices."""
    quality_id = request.GET.get('quality_id', '')
    customer_type = request.GET.get('customer_type', 'retail')
    
    if not quality_id:
        return JsonResponse({'success': False, 'message': 'Quality ID is required.'})
    
    try:
        quality = ProductQuality.objects.get(id=quality_id)
        
        if customer_type == 'retail':
            price = quality.retail_price
        elif customer_type == 'wholesale':
            price = quality.wholesale_price
        elif customer_type == 'broker':
            price = quality.broker_price
        else:
            price = quality.retail_price
        
        return JsonResponse({
            'success': True,
            'price': float(price),
            'stock': float(quality.stock_quantity),
        })
    except ProductQuality.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product quality not found.'})

@login_required
@executive_required
def product_search_api(request):
    """API view for searching products."""
    query = request.GET.get('q', '')
    logger.info(f"Product search query: {query}")
    
    if not query or len(query) < 2:
        logger.warning("Product search query too short or empty")
        return JsonResponse({'products': [], 'message': 'Please enter at least 2 characters to search'})
    
    try:
        # Search by name only (removed sku reference)
        products = Product.objects.filter(name__icontains=query)[:10]
        
        logger.info(f"Found {products.count()} products matching '{query}'")
        
        product_list = []
        for product in products:
            qualities = []
            for quality in product.qualities.all():
                qualities.append({
                    'id': quality.id,
                    'name': quality.get_quality_display(),
                    'retail_price': float(quality.retail_price),
                    'wholesale_price': float(quality.wholesale_price),
                    'broker_price': float(quality.broker_price),
                    'stock_quantity': float(quality.stock_quantity),
                })
            
            product_list.append({
                'id': product.id,
                'name': product.name,
                'image_url': product.image_url if hasattr(product, 'image_url') else None,
                'qualities': qualities,
            })
        
        return JsonResponse({'products': product_list})
    except Exception as e:
        logger.error(f"Error in product search: {str(e)}")
        return JsonResponse({'products': [], 'message': f'Error: {str(e)}'}, status=500)

@login_required
@executive_required
def set_invoice_due_date(request, pk):
    """View for setting or updating an invoice's due date."""
    invoice = get_object_or_404(Invoice, pk=pk)
    
    if invoice.status == 'paid' or invoice.status == 'cancelled':
        messages.warning(request, 'Cannot set due date for paid or cancelled invoices.')
        return redirect('invoice_detail', pk=invoice.pk)
    
    if request.method == 'POST':
        due_date = request.POST.get('due_date')
        try:
            # Parse the date from the form
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            
            # Update the invoice
            invoice.due_date = due_date
            invoice.save()
            
            messages.success(request, 'Due date updated successfully.')
            return redirect('invoice_detail', pk=invoice.pk)
        except (ValueError, TypeError):
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD format.')
    
    # For GET requests or if there's an error in POST
    return render(request, 'billing/set_due_date.html', {
        'invoice': invoice,
    })
