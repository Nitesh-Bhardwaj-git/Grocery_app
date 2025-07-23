from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.decorators import action
from django.contrib.auth.models import User
from .models import Item, Cart, CartItem, Order
from .serializers import ItemSerializer, CartSerializer, CartItemSerializer, OrderSerializer
import requests
from rest_framework.views import APIView
from rest_framework import serializers
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

# API key for image fetch
IMAGE_API_KEY = 'S5UlCFXWXWthgRO08bQsntE4i84da-jRfEyRJT6F4_o'
IMAGE_API_URL = 'https://api.unsplash.com/photos/random'

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

    def perform_create(self, serializer):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        # Only add if not already in cart
        if not CartItem.objects.filter(cart=cart, item=serializer.validated_data['item']).exists():
            serializer.save(cart=cart)

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
        order.items.set(cart_items)
        order.save()
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
    for value, label in categories:
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
    items = CartItem.objects.filter(cart=cart)
    return render(request, 'Grocery_api/cart.html', {'cart_items': items})

@login_required
def orders_page(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'Grocery_api/orders.html', {'orders': orders})

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
