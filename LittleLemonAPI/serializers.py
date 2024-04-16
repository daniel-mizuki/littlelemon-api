import datetime
from decimal import Decimal

import bleach
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator

from .models import (
    MenuItem,
    Category,
    Cart,
    CartItem,
    Order,
    OrderItem,
)
from .fields import SerializerMethodDecimalField


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "id",
            "title",
        ]
        extra_kwargs = {
            "title": {"validators": [UniqueValidator(queryset=Category.objects.all())]},
        }

    def validate_title(self, value):
        return bleach.clean(value)


class MenuItemSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField()
    category = serializers.StringRelatedField(read_only=True)
    featured = serializers.BooleanField(default=False)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "title",
            "price",
            "category_id",
            "category",
            "featured",
        ]
        extra_kwargs = {
            "title": {"validators": [UniqueValidator(queryset=MenuItem.objects.all())]},
            "price": {"min_value": Decimal(0.0)},
        }

    def validate_title(self, value):
        return bleach.clean(value)

    def validate_category_id(self, value):
        if not Category.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid category ID")
        return value


class CartSerializer(serializers.ModelSerializer):
    cart_items = serializers.StringRelatedField(many=True, read_only=True)
    total = SerializerMethodDecimalField(
        method_name="get_total", max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = Cart
        fields = [
            "id",
            "user",
            "cart_items",
            "total",
        ]
        extra_kwargs = {
            "user": {"validators": [UniqueValidator(queryset=Cart.objects.all())]},
        }

    def get_total(self, obj):
        total = Decimal(0.0)
        for item in obj.cart_items.all():
            total += item.menu_item.price * item.quantity
        return total


class CartItemSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    menu_item_id = serializers.IntegerField()
    menu_item = serializers.StringRelatedField(read_only=True)
    unit_price = serializers.DecimalField(
        source="menu_item.price", max_digits=6, decimal_places=2, read_only=True
    )
    price = SerializerMethodDecimalField(
        method_name="get_price", max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = CartItem
        fields = [
            "id",
            "user",
            "menu_item_id",
            "menu_item",
            "quantity",
            "unit_price",
            "price",
        ]
        read_only_fields = ["user"]
        extra_kwargs = {
            "quantity": {"min_value": 1},
        }
        validators = [
            UniqueTogetherValidator(
                queryset=CartItem.objects.all(),
                fields=["user", "menu_item_id"],
            )
        ]

    def validate_menu_item_id(self, value):
        if not MenuItem.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid menu item ID")
        return value

    def get_price(self, obj):
        return obj.menu_item.price * obj.quantity

    def create(self, validated_data):
        user = validated_data["user"]
        cart = user.cart if hasattr(user, "cart") else Cart.objects.create(user=user)

        return CartItem.objects.create(cart=cart, **validated_data)


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(
        default=serializers.CreateOnlyDefault(serializers.CurrentUserDefault())
    )
    order_items = serializers.StringRelatedField(many=True, read_only=True)
    total = SerializerMethodDecimalField(
        method_name="get_total", max_digits=6, decimal_places=2, read_only=True
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "delivery_crew",
            "status",
            "date",
            "order_items",
            "total",
        ]

    def get_total(self, obj):
        total = Decimal(0.0)
        for item in obj.order_items.all():
            total += item.price

        return total

    def validate_user(self, value):
        if not value.cart_items.exists():
            raise serializers.ValidationError(
                "Cannot create order for user with an empty cart"
            )

        return value

    def validate_delivery_crew(self, value):
        if not value.groups.filter(name="Delivery Crew").exists():
            raise serializers.ValidationError("Invalid delivery crew ID")
        return value

    def create(self, validated_data):
        order = Order.objects.create(**validated_data)
        user = validated_data["user"]

        for item in user.cart_items.all():
            OrderItem.objects.create(
                order=order,
                menu_item=item.menu_item,
                quantity=item.quantity,
                unit_price=item.menu_item.price,
                price=item.menu_item.price * item.quantity,
            )

        user.cart.delete()

        return order


class GroupUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
        ]


class HiddenFieldSerializerMixin:
    hidden_fields = []

    def get_fields(self):
        fields = super().get_fields()
        for field in self.hidden_fields:
            fields.pop(field, None)
        return fields
