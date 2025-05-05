import pandas as pd
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from authentication.decorators import admin_required, executive_required
from .models import Product, ProductQuality, PriceList
from .forms import ProductForm, ProductQualityForm, PriceListUploadForm, ProductSearchForm
from .utils import generate_price_list_template

logger = logging.getLogger(__name__)

@login_required
@executive_required
def product_list(request):
    """View for listing all products."""
    form = ProductSearchForm(request.GET)
    products = Product.objects.all()
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
    
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'products/product_list.html', {
        'page_obj': page_obj,
        'form': form,
    })

@login_required
@executive_required
def product_detail(request, pk):
    """View for displaying product details."""
    product = get_object_or_404(Product, pk=pk)
    qualities = product.qualities.all()
    
    return render(request, 'products/product_detail.html', {
        'product': product,
        'qualities': qualities,
    })

@login_required
@admin_required
def product_create(request):
    """View for creating a new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Product created successfully!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Create Product',
    })

@login_required
@admin_required
def product_update(request, pk):
    """View for updating an existing product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Update Product',
        'product': product,
    })

@login_required
@admin_required
def product_delete(request, pk):
    """View for deleting a product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('product_list')
    
    return render(request, 'products/product_confirm_delete.html', {
        'product': product,
    })

@login_required
@admin_required
def quality_create(request, product_pk):
    """View for adding a quality variant to a product."""
    product = get_object_or_404(Product, pk=product_pk)
    
    if request.method == 'POST':
        form = ProductQualityForm(request.POST)
        if form.is_valid():
            quality = form.save(commit=False)
            quality.product = product
            quality.save()
            messages.success(request, 'Quality variant added successfully!')
            return redirect('product_detail', pk=product.pk)
    else:
        form = ProductQualityForm()
    
    return render(request, 'products/quality_form.html', {
        'form': form,
        'title': f'Add Quality Variant - {product.name}',
        'product': product,
    })

@login_required
@admin_required
def quality_update(request, pk):
    """View for updating a quality variant."""
    quality = get_object_or_404(ProductQuality, pk=pk)
    
    if request.method == 'POST':
        form = ProductQualityForm(request.POST, instance=quality)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quality variant updated successfully!')
            return redirect('product_detail', pk=quality.product.pk)
    else:
        form = ProductQualityForm(instance=quality)
    
    return render(request, 'products/quality_form.html', {
        'form': form,
        'title': f'Update Quality Variant - {quality.product.name}',
        'product': quality.product,
        'quality': quality,
    })

@login_required
@admin_required
def quality_delete(request, pk):
    """View for deleting a quality variant."""
    quality = get_object_or_404(ProductQuality, pk=pk)
    product_pk = quality.product.pk
    
    if request.method == 'POST':
        quality.delete()
        messages.success(request, 'Quality variant deleted successfully!')
        return redirect('product_detail', pk=product_pk)
    
    return render(request, 'products/quality_confirm_delete.html', {
        'quality': quality,
    })

@login_required
@admin_required
def price_list_upload(request):
    """View for uploading price lists."""
    if request.method == 'POST':
        form = PriceListUploadForm(request.POST, request.FILES)
        if form.is_valid():
            price_list = form.save(commit=False)
            price_list.uploaded_by = request.user
            price_list.save()
            
            try:
                process_price_list(price_list)
                messages.success(request, 'Price list uploaded and processed successfully!')
            except Exception as e:
                messages.error(request, f'Error processing price list: {str(e)}')
                logger.error(f"Price list processing error: {str(e)}", exc_info=True)
            
            return redirect('product_list')
    else:
        form = PriceListUploadForm()
    
    return render(request, 'products/price_list_upload.html', {
        'form': form,
    })

def process_price_list(price_list):
    """Process the uploaded price list Excel file."""
    try:
        # Read the Excel file - no header parameter needed now since we removed the instruction row
        df = pd.read_excel(price_list.file.path)
        
        # Debug: Print all column names found in the file
        logger.info(f"Columns found in Excel file: {list(df.columns)}")
        
        # Define required columns and their possible alternative names
        column_mapping = {
            'Product Name': ['product name', 'product', 'name', 'item name', 'item'],
            'Quality': ['quality', 'grade', 'variant', 'type'],
            'Retail Price': ['retail price', 'retail', 'mrp', 'price'],
            'Wholesale Price': ['wholesale price', 'wholesale', 'bulk price'],
            'Broker Price': ['broker price', 'broker', 'agent price', 'distributor price']
        }
        
        # Standardize column names (convert to lowercase for case-insensitive matching)
        df.columns = [str(col).strip() for col in df.columns]
        
        # Create a mapping from actual columns to standard column names
        actual_to_standard = {}
        for standard_col, alternatives in column_mapping.items():
            found = False
            for alt in [standard_col.lower()] + alternatives:
                matching_cols = [col for col in df.columns if col.lower() == alt]
                if matching_cols:
                    actual_to_standard[matching_cols[0]] = standard_col
                    found = True
                    break
            
            if not found:
                # List all columns found in the file to help with debugging
                found_cols = ", ".join(df.columns)
                raise ValueError(f"Missing required column: {standard_col}. Columns found: {found_cols}")
        
        # Rename columns to standard names
        df = df.rename(columns=actual_to_standard)
        
        # Check if we have all required columns after mapping
        for required_col in ['Product Name', 'Quality', 'Retail Price', 'Wholesale Price', 'Broker Price']:
            if required_col not in df.columns:
                raise ValueError(f"Missing required column after mapping: {required_col}")
        
        # Process each row in the Excel file
        processed_count = 0
        for _, row in df.iterrows():
            # Skip rows with empty product names
            if pd.isna(row['Product Name']) or str(row['Product Name']).strip() == '':
                continue
                
            product_name = str(row['Product Name']).strip()
            quality = str(row['Quality']).lower().strip()
            
            # Convert prices to float, handling any non-numeric values
            try:
                retail_price = float(row['Retail Price'])
                wholesale_price = float(row['Wholesale Price'])
                broker_price = float(row['Broker Price'])
            except (ValueError, TypeError):
                raise ValueError(f"Invalid price value for product '{product_name}'. Prices must be numbers.")
            
            # Handle stock quantity if present
            stock_quantity = 0
            if 'Stock Quantity' in df.columns and not pd.isna(row['Stock Quantity']):
                try:
                    stock_quantity = float(row['Stock Quantity'])
                except (ValueError, TypeError):
                    stock_quantity = 0
            
            # Get or create the product
            product, _ = Product.objects.get_or_create(name=product_name)
            
            # Get or create the quality variant
            quality_obj, created = ProductQuality.objects.get_or_create(
                product=product,
                quality=quality,
                defaults={
                    'retail_price': retail_price,
                    'wholesale_price': wholesale_price,
                    'broker_price': broker_price,
                    'stock_quantity': stock_quantity,
                }
            )
            
            # If the quality variant already exists, update its prices
            if not created:
                quality_obj.retail_price = retail_price
                quality_obj.wholesale_price = wholesale_price
                quality_obj.broker_price = broker_price
                quality_obj.stock_quantity = stock_quantity
                quality_obj.save()
            
            processed_count += 1
        
        if processed_count == 0:
            raise ValueError("No valid product data found in the file. Please check the format and try again.")
        
        # Mark the price list as processed
        price_list.processed = True
        price_list.save()
        
        logger.info(f"Successfully processed {processed_count} products from price list")
        
    except Exception as e:
        logger.error(f"Error processing price list: {str(e)}", exc_info=True)
        raise

@login_required
@executive_required
def product_search_api(request):
    """API view for searching products."""
    query = request.GET.get('q', '')
    
    if not query:
        return JsonResponse({'products': []})
    
    # Search by name
    products = Product.objects.filter(name__icontains=query)[:10]
    
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
            'qualities': qualities,
        })
    
    return JsonResponse({'products': product_list})

@login_required
@admin_required
def download_price_list_template(request):
    """View to download the price list Excel template."""
    output = generate_price_list_template()
    
    # Create the HttpResponse with appropriate headers
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="price_list_template.xlsx"'
    
    return response
