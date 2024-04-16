from django.db.models import Q
from django.contrib.auth.models import User, Group
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
from slugify import slugify

from .models import (
    MenuItem,
    Category,
    Cart,
    CartItem,
    Order,
)
from .serializers import (
    MenuItemSerializer,
    CategorySerializer,
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    GroupUserSerializer,
    HiddenFieldSerializerMixin,
)
from .permissions import DjangoModelPermissionsStrict, IsCreate


class MenuItemViewSet(ModelViewSet):
    permission_classes = [DjangoModelPermissions]
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    ordering_fields = ["id", "price"]
    ordering = ["id"]
    search_fields = ["title", "category__title"]
    filterset_fields = ["category", "featured"]


class CategoryViewSet(ModelViewSet):
    permission_classes = [DjangoModelPermissions]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering_fields = ["id"]
    ordering = ["id"]
    search_fields = ["title"]


class CartViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartSerializer
    ordering_fields = ["id", "total"]
    ordering = ["id"]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


class CartItemViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer
    ordering_fields = ["id", "quantity"]
    ordering = ["id"]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    @action(detail=False, methods=["DELETE"])
    def destroy_all(self, request):
        user = request.user
        if hasattr(user, "cart"):
            user.cart.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(ModelViewSet):
    permission_classes = [DjangoModelPermissions | IsCreate]
    serializer_class = OrderSerializer
    ordering_fields = ["id", "date", "total"]
    ordering = ["id"]
    filterset_fields = ["delivery_crew", "status"]

    def get_queryset(self):
        if self.request.user.groups.filter(name="Manager").exists():
            return Order.objects.all()
        if self.request.user.groups.filter(name="Delivery Crew").exists():
            return Order.objects.filter(
                Q(user=self.request.user) | Q(delivery_crew=self.request.user)
            )
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        hidden_fields = []

        if self.request.method == "POST":
            hidden_fields.append("delivery_crew")
            hidden_fields.append("status")
        elif (
            self.request.method in ["PUT", "PATCH"]
            and self.request.user.groups.filter(name="Delivery Crew").exists()
        ):
            hidden_fields.append("delivery_crew")

        return type(
            "OrderHiddenFieldSerializer",
            (HiddenFieldSerializerMixin, OrderSerializer),
            {"hidden_fields": hidden_fields},
        )


class GroupUserViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    permission_classes = [DjangoModelPermissionsStrict]
    serializer_class = GroupUserSerializer
    ordering_fields = ["id"]
    ordering = ["id"]
    search_fields = ["username"]
    group = None

    def initialize_request(self, request, *args, **kwargs):
        for group in Group.objects.all():
            if slugify(group.name) == kwargs["group_name"]:
                self.group = group
                break

        if not self.group:
            raise Http404("Group not found")

        return super().initialize_request(request, *args, **kwargs)

    def get_queryset(self):
        return self.group.user_set.all()

    def create(self, request, *args, **kwargs):
        user = get_object_or_404(User, username=request.data["username"])
        self.group.user_set.add(user)

        content = {"message": "User added to group"}
        return Response(content, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        user = get_object_or_404(queryset, pk=kwargs["pk"])
        self.group.user_set.remove(user)

        content = {"message": "User removed from group"}
        return Response(content, status=status.HTTP_200_OK)
