from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemViewSet, CartViewSet, CartItemViewSet, OrderViewSet, UserRegisterView,
    home, user_login, user_register, user_logout, cart_page, orders_page, add_item
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'items', ItemViewSet)
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cartitem')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    # HTML pages first!
    path('', home, name='home'),
    path('login/', user_login, name='login'),
    path('register/', user_register, name='register'),
    path('logout/', user_logout, name='logout'),
    path('cart/', cart_page, name='cart'),
    path('orders/', orders_page, name='orders'),
    path('add-item/', add_item, name='add_item'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/register/', UserRegisterView.as_view(), name='user_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 