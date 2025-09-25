# 🛒 Grocery App

A modern, full-featured grocery shopping application built with Django and Django REST Framework. This application allows users to browse products, manage shopping carts, create wishlists, and place orders.

## ✨ Features

### 🛍️ Shopping Features
- **Product Catalog**: Browse products organized by categories (Fruits, Vegetables, Dairy, Bakery, Beverages, Snacks, Other)
- **Search Functionality**: Search products by name or description
- **Shopping Cart**: Add items to cart, adjust quantities, and manage cart contents
- **Wishlist**: Save items to wishlist for future reference
- **Order Management**: Place orders and view order history

### 👤 User Management
- **User Registration & Authentication**: Secure user registration and login system
- **User Profiles**: Manage user account information
- **Admin Panel**: Comprehensive admin interface for product and order management

### 🎨 User Interface
- **Responsive Design**: Modern, mobile-friendly interface using Tailwind CSS
- **Category Navigation**: Easy category filtering with dropdown navigation
- **Product Images**: Automatic image fetching from Unsplash API
- **Real-time Updates**: Dynamic cart and wishlist counters

### 🔧 Technical Features
- **REST API**: Full REST API with JWT authentication
- **Database Support**: PostgreSQL for production, SQLite for development
- **Environment Configuration**: Secure environment variable management
- **Search & Filter**: Advanced product search and category filtering

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (for production)
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Grocery
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://username:password@host:port/database
   # Optional: control Django debug
   DEBUG=True
   # Unsplash API key for product images
   IMAGE_API_KEY=your-unsplash-access-key
   # Optional: auto-create superuser (used by `python manage.py createsu`)
   DJANGO_SUPERUSER_USERNAME=admin
   DJANGO_SUPERUSER_EMAIL=admin@example.com
   DJANGO_SUPERUSER_PASSWORD=your-secure-password
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main app: http://localhost:8000
   - Admin panel: http://localhost:8000/admin



## 🗄️ Database Models

### Core Models
- **Item**: Products with name, description, price, category, and unit information
- **Cart**: User shopping carts
- **CartItem**: Individual items in carts with quantities
- **Order**: User orders with total pricing
- **Wishlist**: User wishlists
- **WishlistItem**: Individual items in wishlists

## 🔌 API Endpoints

### Authentication
- `POST /api/token/` - Obtain JWT token
- `POST /api/token/refresh/` - Refresh JWT token
- `POST /api/register/` - User registration

### Products
- `GET /api/items/` - List all products
- `POST /api/items/` - Create new product (admin only)
- `GET /api/items/{id}/` - Get product details
- `PUT /api/items/{id}/` - Update product (admin only)
- `DELETE /api/items/{id}/` - Delete product (admin only)

### Cart
- `GET /api/cart/mycart/` - Get user's cart
- `POST /api/cart-items/` - Add item to cart
- `PUT /api/cart-items/{id}/` - Update cart item
- `DELETE /api/cart-items/{id}/` - Remove item from cart

### Orders
- `GET /api/orders/` - List user's orders
- `POST /api/orders/checkout/` - Create order from cart

## 🌐 Deployment

### Render Deployment

1. **Connect your repository** to Render
2. **Set environment variables** in Render dashboard:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SECRET_KEY`: Django secret key
   - `DJANGO_SUPERUSER_USERNAME`: Admin username
   - `DJANGO_SUPERUSER_EMAIL`: Admin email
   - `DJANGO_SUPERUSER_PASSWORD`: Admin password

3. **Build Command**:
   ```bash
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py createsu
   ```

4. **Start Command**:
   ```bash
   gunicorn Grocery.wsgi:application
   ```

## 📱 Usage

### For Users
1. **Register/Login**: Create an account or log in
2. **Browse Products**: View products by category or search
3. **Add to Cart**: Click "Add to Cart" on any product
4. **Manage Cart**: Adjust quantities or remove items
5. **Checkout**: Complete your order
6. **View Orders**: Check your order history

### For Administrators
1. **Access Admin Panel**: Go to `/admin` and log in
2. **Manage Products**: Add, edit, or delete products
3. **View Orders**: Monitor all user orders
4. **User Management**: Manage user accounts

## 🔧 Configuration

### Categories
Product categories are defined in `models.py`:
- Fruits
- Vegetables
- Dairy
- Bakery
- Beverages
- Snacks
- Other

### Units
Supported product units:
- kg (Kilogram)
- g (Gram)
- litre (Litre)
- ml (Millilitre)
- pcs (Pieces)
- pack (Pack)
- other (Other)

