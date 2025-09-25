from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ItemViewSet, CartViewSet, CartItemViewSet, OrderViewSet, UserRegisterView,
    home, user_login, user_register, user_logout, cart_page, orders_page, add_item, edit_item, delete_item, checkout, move_to_wishlist, wishlist_page, move_to_cart, product_detail, profile_page, add_to_wishlist, create_superuser_view
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
    path('orders/checkout/', checkout, name='checkout'),
    path('add-item/', add_item, name='add_item'),
    path('edit-item/<int:item_id>/', edit_item, name='edit_item'),
    path('delete-item/<int:item_id>/', delete_item, name='delete_item'),
    path('cart/move-to-wishlist/<int:cart_item_id>/', move_to_wishlist, name='move_to_wishlist'),
    path('wishlist/', wishlist_page, name='wishlist'),
    path('wishlist/move-to-cart/<int:wishlist_item_id>/', move_to_cart, name='move_to_cart'),
    path('wishlist/add/<int:item_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('item/<int:item_id>/', product_detail, name='product_detail'),
    path('profile/', profile_page, name='profile'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/register/', UserRegisterView.as_view(), name='user_register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
] 