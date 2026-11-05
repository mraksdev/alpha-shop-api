from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum


class Cart(models.Model):
    """Shopping cart of a user."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='пользователь',
    )
    created = models.DateTimeField('дата создания', auto_now_add=True)
    updated = models.DateTimeField('дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'корзины'
        ordering = ('-updated',)

    def __str__(self) -> str:
        return 'Корзина {}'.format(self.user)

    def get_total_quantity(self) -> int:
        """Return the total number of products in the cart."""
        return self.items.aggregate(total=Sum('quantity'))['total'] or 0

    def get_total_price(self):
        """Return the total price of all products in the cart."""
        total = self.items.aggregate(
            total=Sum(F('quantity') * F('product__price')),
        )['total']
        return round(total or Decimal('0.00'), 2)


class CartItem(models.Model):
    """Product with its quantity inside a cart."""

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='корзина',
    )
    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name='продукт',
    )
    quantity = models.PositiveSmallIntegerField(
        'количество',
        validators=[MinValueValidator(1)],
    )

    class Meta:
        verbose_name = 'позиция корзины'
        verbose_name_plural = 'позиции корзины'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('cart', 'product'),
                name='unique_cart_product',
            ),
        ]

    def __str__(self) -> str:
        return '{} x {}'.format(self.product.name, self.quantity)

    @property
    def total_price(self):
        """Return the price of this cart item."""
        return self.product.price * self.quantity
