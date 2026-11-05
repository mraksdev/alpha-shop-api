from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline editor for products inside a cart."""

    model = CartItem
    extra = 1
    fields = ('product', 'quantity', 'total_price')
    readonly_fields = ('total_price',)

    @admin.display(description='стоимость')
    def total_price(self, obj):
        """Return the price of the cart item."""
        if not obj.product_id:
            return '—'
        return obj.total_price


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin panel for carts."""

    list_display = (
        'id',
        'user',
        'total_quantity',
        'total_price',
        'created',
        'updated',
    )
    search_fields = ('user__email', 'user__username')
    list_select_related = ('user',)
    readonly_fields = ('created', 'updated')
    inlines = (CartItemInline,)

    @admin.display(description='товаров')
    def total_quantity(self, obj):
        """Return the total number of products in the cart."""
        return obj.get_total_quantity()

    @admin.display(description='сумма')
    def total_price(self, obj):
        """Return the total price of the cart."""
        return obj.get_total_price()


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin panel for cart items."""

    list_display = (
        'id',
        'cart',
        'product',
        'quantity',
        'total_price',
    )
    list_select_related = ('cart__user', 'product')
    search_fields = ('cart__user__email', 'product__name')
    list_filter = ('cart__user',)

    @admin.display(description='стоимость')
    def total_price(self, obj):
        """Return the price of the cart item."""
        return obj.total_price
