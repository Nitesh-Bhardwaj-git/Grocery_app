from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .models import Item, Cart, CartItem, Order, OrderItem, Wishlist, WishlistItem
from .serializers import ItemSerializer, CartSerializer, CartItemSerializer, OrderSerializer
import requests
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
import os

# API key for image fetch
IMAGE_API_KEY = 'S5UlCFXWXWthgRO08bQsntE4i84da-jRfEyRJT6F4_o'
IMAGE_API_URL = 'https://api.unsplash.com/photos/random'

def create_superuser_view(request):
    """
    View to create a superuser during deployment
    This should be called once during deployment setup
    """
    if request.method == 'POST':
        # Get credentials from environment variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not all([username, email, password]):
            return JsonResponse({
                'success': False,
                'error': 'Missing environment variables: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD'
            }, status=400)
        
        try:
            # Check if superuser already exists
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': True,
                    'message': f'Superuser "{username}" already exists'
                })
            
            # Create superuser
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Superuser "{username}" created successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error creating superuser: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Only POST method is allowed'
    }, status=405)

def fetch_image_url(query):
    IMAGE_API_KEY = 'S5UlCFXWXWthgRO08bQsntE4i84da-jRfEyRJT6F4_o'
    SEARCH_API_URL = 'https://api.unsplash.com/search/photos'
    params = {
        'query': query,
        'client_id': IMAGE_API_KEY,
        'orientation': 'squarish',
        'per_page': 1,
    }
    try:
        resp = requests.get(SEARCH_API_URL, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', [])
            if results and 'urls' in results[0] and 'small' in results[0]['urls']:
                return results[0]['urls']['small']
        print(f'Unsplash API error or no image found for query: {query}, response: {resp.text}')
        return 'https://via.placeholder.com/150?text=No+Image'
    except Exception as e:
        print(f'Error fetching image for {query}: {e}')
        return 'https://via.placeholder.com/150?text=No+Image'

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().order_by('-created_at')
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        name = self.request.data.get('name', '')
        image_url = fetch_image_url(name)
        serializer.save(image_url=image_url)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def mycart(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)

    def create(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item = request.data.get('item_id')
        try:
            quantity = max(1, int(request.data.get('quantity', 1)))
        except (ValueError, TypeError):
            quantity = 1
        
        if not item:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item_obj = Item.objects.get(id=item)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, 
            item=item_obj,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # If item already exists, update quantity
            cart_item.quantity = max(1, cart_item.quantity + quantity)
            cart_item.save()
        
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        if not cart_items.exists():
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)
        total = sum([item.item.price * item.quantity for item in cart_items])
        order = Order.objects.create(user=request.user, total_price=total)
        
        # Create OrderItems from CartItems
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                name=cart_item.item.name,
                image_url=cart_item.item.image_url,
                quantity=cart_item.quantity,
                price=cart_item.item.price
            )
        
        cart_items.delete()  # Clear cart
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'password']
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class UserRegisterView(APIView):
    permission_classes = []
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'User created successfully.'}, status=201)
        return Response(serializer.errors, status=400)

@csrf_protect
def home(request):
    categories = Item.CATEGORY_CHOICES
    items_by_category = []
    search_query = request.GET.get('search', '').strip()
    for value, label in categories:
        if search_query:
            items = Item.objects.filter(category=value).filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )
        else:
            items = Item.objects.filter(category=value)
        items_by_category.append({'label': label, 'items': items})
    return render(request, 'Grocery_api/home.html', {'items_by_category': items_by_category})

@csrf_protect
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'Grocery_api/login.html')

@csrf_protect
def user_register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if not username or not email or not password or not confirm_password:
            messages.error(request, 'All fields are required')
        elif password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    return render(request, 'Grocery_api/register.html')

@login_required
def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def cart_page(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        cart_item_id = request.POST.get('cart_item_id')
        action = request.POST.get('action')
        if cart_item_id and action:
            cart_item = get_object_or_404(CartItem, id=cart_item_id, cart=cart)
            if action == 'increase':
                cart_item.quantity += 1
                cart_item.save()
                messages.success(request, f"Increased quantity of {cart_item.item.name}.")
            elif action == 'decrease':
                if cart_item.quantity > 1:
                    cart_item.quantity -= 1
                    cart_item.save()
                    messages.success(request, f"Decreased quantity of {cart_item.item.name}.")
                else:
                    cart_item.delete()
                    messages.success(request, f"Removed {cart_item.item.name} from cart.")
            return redirect('cart')
        remove_cart_item_id = request.POST.get('remove_cart_item_id')
        if remove_cart_item_id:
            cart_item = get_object_or_404(CartItem, id=remove_cart_item_id, cart=cart)
            cart_item.delete()
            messages.success(request, f"Removed {cart_item.item.name} from cart.")
            return redirect('cart')
        item_id = request.POST.get('item_id')
        if item_id:
            item = get_object_or_404(Item, id=item_id)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item)
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            messages.success(request, f"{item.name} added to cart!")
        return redirect('cart')
    items = CartItem.objects.filter(cart=cart)
    return render(request, 'Grocery_api/cart.html', {'cart_items': items})

@login_required
def orders_page(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'Grocery_api/orders.html', {'orders': orders})

@login_required
@csrf_protect
def checkout(request):
    if request.method == 'POST':
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        if not cart_items.exists():
            messages.error(request, 'Cart is empty.')
            return redirect('cart')
        total = sum([item.item.price * item.quantity for item in cart_items])
        order = Order.objects.create(user=request.user, total_price=total)
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                name=cart_item.item.name,
                image_url=cart_item.item.image_url,
                quantity=cart_item.quantity,
                price=cart_item.item.price
            )
        cart_items.delete()  # Clear cart
        messages.success(request, 'Order placed successfully!')
        return redirect('orders')
    return redirect('cart')

@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
def add_item(request):
    from .views import fetch_image_url
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        price = request.POST['price']
        category = request.POST['category']
        unit = request.POST.get('unit', 'pcs')
        unit_value = request.POST.get('unit_value', 1)
        image_url = fetch_image_url(name)
        Item.objects.create(name=name, description=description, price=price, category=category, unit=unit, unit_value=unit_value, image_url=image_url)
        messages.success(request, 'Item added!')
        return redirect('home')
    categories = Item.CATEGORY_CHOICES
    units = Item.UNIT_CHOICES
    return render(request, 'Grocery_api/add_item.html', {'categories': categories, 'units': units})

@user_passes_test(lambda u: u.is_superuser)
@csrf_protect
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        item.name = request.POST['name']
        item.description = request.POST['description']
        item.price = request.POST['price']
        item.category = request.POST['category']
        item.unit = request.POST['unit']
        item.unit_value = request.POST.get('unit_value', 1)
        item.save()
        messages.success(request, 'Item updated!')
        return redirect('home')
    categories = Item.CATEGORY_CHOICES
    units = Item.UNIT_CHOICES
    return render(request, 'Grocery_api/edit_item.html', {'item': item, 'categories': categories, 'units': units})

@user_passes_test(lambda u: u.is_superuser)
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted!')
        return redirect('home')
    return render(request, 'Grocery_api/delete_item.html', {'item': item})

@login_required
def move_to_wishlist(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, cart__user=request.user)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, item=cart_item.item)
    if not created:
        wishlist_item.quantity += cart_item.quantity
        wishlist_item.save()
    else:
        wishlist_item.quantity = cart_item.quantity
        wishlist_item.save()
    cart_item.delete()
    messages.success(request, f"Moved {wishlist_item.item.name} to wishlist.")
    return redirect('cart')

@login_required
def wishlist_page(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    items = WishlistItem.objects.filter(wishlist=wishlist)
    return render(request, 'Grocery_api/wishlist.html', {'wishlist_items': items})

@login_required
def move_to_cart(request, wishlist_item_id):
    wishlist_item = get_object_or_404(WishlistItem, id=wishlist_item_id, wishlist__user=request.user)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=wishlist_item.item)
    if not created:
        cart_item.quantity += wishlist_item.quantity
        cart_item.save()
    else:
        cart_item.quantity = wishlist_item.quantity
        cart_item.save()
    wishlist_item.delete()
    messages.success(request, f"Moved {cart_item.item.name} to cart.")
    return redirect('wishlist')

@login_required
def product_detail(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    return render(request, 'Grocery_api/product_detail.html', {'item': item})

@login_required
def profile_page(request):
    user = request.user
    return render(request, 'Grocery_api/profile.html', {'user': user})

@login_required
def add_to_wishlist(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist_item, created = WishlistItem.objects.get_or_create(wishlist=wishlist, item=item)
    if not created:
        wishlist_item.quantity += 1
        wishlist_item.save()
    else:
        wishlist_item.quantity = 1
        wishlist_item.save()
    messages.success(request, f"Added {item.name} to wishlist.")
    return redirect('home')

def global_counts(request):
    cart_items = []
    wishlist_items = []
    if request.user.is_authenticated:
        try:
            cart, _ = Cart.objects.get_or_create(user=request.user)
            cart_items = CartItem.objects.filter(cart=cart)
        except:
            pass
        try:
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            wishlist_items = WishlistItem.objects.filter(wishlist=wishlist)
        except:
            pass
    return {'cart_items': cart_items, 'wishlist_items': wishlist_items}
