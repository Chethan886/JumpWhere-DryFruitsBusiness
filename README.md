# JumpWhere-DryFruitsBusiness
# Dry Fruits Business Management System

A comprehensive Django-based business management system designed for dry fruits wholesalers and distributors. This application helps manage customers, products, invoices, payments, and generates business reports.

## System Requirements

- Python 3.8+
- MySQL 5.7+ or SQLite (for development)
- pip (Python package manager)
- Virtual environment tool (venv or virtualenv)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dry-fruits-business.git
cd dry-fruits-business


# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate


pip install -r requirements.txt


## Create Django Project
```bash
django-admin startproject dry_fruits_project

# Navigate to project directory
cd JumpWhere-DryFruitsBusiness

# Create Django apps
python manage.py startapp authentication
python manage.py startapp customers
python manage.py startapp products
python manage.py startapp billing
python manage.py startapp payments
python manage.py startapp reports



## Running the Application

### 1. Apply Migrations

```shell
python manage.py migrate
```

### 2. Create Superuser

```shell
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

### 3. Run Development Server

```shell
python manage.py runserver
```

The application will be available at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 4. Access Admin Interface

Visit [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) and log in with the superuser credentials.

## Key Features

### User Management

- Custom user model with role-based permissions
- User authentication and authorization
- User creation and management

### Customer Management

- Customer database with contact information
- Customer financial history
- Customer categorization

### Product Management

- Product catalog with multiple quality variants
- Price management
- Bulk price list import/export via Excel

### Billing System

- Invoice creation and management
- Item-based invoicing with discounts
- PDF invoice generation
- Invoice status tracking

### Payment Tracking

- Payment recording against invoices
- Pending payment tracking
- Payment history

### Reporting

- Sales reports
- Customer payment reports
- Product performance reports
