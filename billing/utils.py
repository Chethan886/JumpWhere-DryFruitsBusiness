from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_invoice_pdf(invoice, items):
    """Generate a PDF for the given invoice using ReportLab instead of WeasyPrint."""
    buffer = BytesIO()
    
    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Company information
    company_name = 'Dry Fruits Business'
    company_address = '123 Business Street, City, Country'
    company_phone = '+1234567890'
    company_email = 'info@dryfruitsbusiness.com'
    
    # Add company header
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph(company_address, normal_style))
    elements.append(Paragraph(f"Phone: {company_phone}", normal_style))
    elements.append(Paragraph(f"Email: {company_email}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add invoice header
    elements.append(Paragraph(f"INVOICE #{invoice.invoice_number}", subtitle_style))
    elements.append(Paragraph(f"Date: {invoice.created_at.strftime('%Y-%m-%d')}", normal_style))
    elements.append(Paragraph(f"Status: {invoice.get_status_display()}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add customer information
    elements.append(Paragraph("Customer Information:", subtitle_style))
    elements.append(Paragraph(f"Name: {invoice.customer.name}", normal_style))
    elements.append(Paragraph(f"Phone: {invoice.customer.phone}", normal_style))
    elements.append(Paragraph(f"Address: {invoice.customer.address}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add invoice items
    elements.append(Paragraph("Invoice Items:", subtitle_style))
    
    # Create table for items
    data = [['#', 'Product', 'Quality', 'Quantity', 'Unit Price', 'Discount', 'Subtotal']]
    
    for i, item in enumerate(items, 1):
        data.append([
            str(i),
            item.product.name,
            item.product_quality.get_quality_display() if item.product_quality else '',
            f"{item.quantity} kg",
            f"₹{item.unit_price:.2f}",
            f"{item.discount_percentage}%",
            f"₹{item.subtotal:.2f}"
        ])
    
    # Add totals
    data.append(['', '', '', '', '', 'Subtotal:', f"₹{invoice.subtotal:.2f}"])
    if invoice.discount_percentage > 0:
        data.append(['', '', '', '', '', f'Discount ({invoice.discount_percentage}%):', f"₹{invoice.discount_amount:.2f}"])
    if invoice.tax_percentage > 0:
        data.append(['', '', '', '', '', f'Tax ({invoice.tax_percentage}%):', f"₹{invoice.tax_amount:.2f}"])
    data.append(['', '', '', '', '', 'Total:', f"₹{invoice.total:.2f}"])
    if invoice.amount_paid > 0:
        data.append(['', '', '', '', '', 'Paid:', f"₹{invoice.amount_paid:.2f}"])
        data.append(['', '', '', '', '', 'Balance:', f"₹{invoice.total - invoice.amount_paid:.2f}"])
    
    # Create the table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add terms and notes
    if invoice.notes:
        elements.append(Paragraph("Notes:", subtitle_style))
        elements.append(Paragraph(invoice.notes, normal_style))
        elements.append(Spacer(1, 0.25*inch))
    
    elements.append(Paragraph("Terms and Conditions:", subtitle_style))
    elements.append(Paragraph("1. Payment is due within 30 days.", normal_style))
    elements.append(Paragraph("2. Please make checks payable to Dry Fruits Business.", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf
