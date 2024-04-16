from django.urls import path, include
from rest_framework import routers

from .views import (
    MenuItemViewSet,
    CategoryViewSet,
    CartViewSet,
    CartItemViewSet,
    OrderViewSet,
    GroupUserViewSet,
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"menu-items", MenuItemViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"orders", OrderViewSet, basename="orders")
router.register(
    r"groups/(?P<group_name>[a-z0-9]+(?:-[a-z0-9]+)*)/users",
    GroupUserViewSet,
    basename="group-users",
)

cart_items = CartItemViewSet.as_view(
    {
        "get": "list",
        "post": "create",
        "delete": "destroy_all",
    }
)
cart_items_detail = CartItemViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)

urlpatterns = [
    path("cart/menu-items", cart_items, name="cart-items"),
    path("cart/menu-items/<int:pk>", cart_items_detail, name="cart-items-detail"),
    path("", include(router.urls)),
]
