from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True, unique=True)

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.title


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Cart {self.id}"


class CartItem(models.Model):
    user = models.ForeignKey(User, related_name="cart_items", on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, related_name="cart_items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()

    class Meta:
        unique_together = ["user", "menu_item"]

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.title} @ {self.menu_item.price} : {self.menu_item.price * self.quantity}"


class Order(models.Model):
    user = models.ForeignKey(User, related_name="orders", on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(
        User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True
    )
    status = models.BooleanField(db_index=True, default=0)
    date = models.DateField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Order {self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="order_items", on_delete=models.CASCADE
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ["order", "menu_item"]

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.title} @ {self.unit_price} : {self.price}"
