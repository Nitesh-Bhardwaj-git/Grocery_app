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
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

# API key for image fetch
IMAGE_API_KEY = 'S5UlCFXWXWthgRO08bQsntE4i84da-jRfEyRJT6F4_o'
IMAGE_API_URL = 'https://api.unsplash.com/photos/random'

def fetch_image_url(query):
    params = {
        'query': query,
        'client_id': IMAGE_API_KEY,
        'orientation': 'squarish',
    }
    try:
        resp = requests.get(IMAGE_API_URL, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data.get('urls', {}).get('small', '')
    except Exception:
        pass
    return ''

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
        password = request.POST['password']
        if not username or not password:
            messages.error(request, 'Username and password required')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(username=username, password=password)
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
        image_url = fetch_image_url(name)
        Item.objects.create(name=name, description=description, price=price, category=category, unit=unit, image_url=image_url)
        messages.success(request, 'Item added!')
        return redirect('home')
    categories = Item.CATEGORY_CHOICES
    units = Item.UNIT_CHOICES
    return render(request, 'Grocery_api/add_item.html', {'categories': categories, 'units': units})
