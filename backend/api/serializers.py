from decimal import Decimal

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from cart.models import Cart, CartItem
from catalog.models import Category, Product, Subcategory


class SubcategorySerializer(serializers.ModelSerializer):
    """Serializer for a subcategory inside a category."""

    class Meta:
        model = Subcategory
        fields = ('id', 'name', 'slug', 'image')


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for a category with its subcategories."""

    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'subcategories')


class CategoryShortSerializer(serializers.ModelSerializer):
    """Short category serializer for products."""

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')


class SubcategoryShortSerializer(serializers.ModelSerializer):
    """Short subcategory serializer for products."""

    class Meta:
        model = Subcategory
        fields = ('id', 'name', 'slug')


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for a product with its catalog information."""

    category = CategoryShortSerializer(read_only=True)
    subcategory = SubcategoryShortSerializer(read_only=True)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        read_only=True,
    )
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'subcategory',
            'price',
            'images',
        )

    def get_images(self, product) -> list[str]:
        """Return URLs of the original, medium and small images."""
        request = self.context.get('request')
        images = []
        images_fields = (
            product.image,
            product.image_medium,
            product.image_small,
        )
        for image in images_fields:
            if not image:
                continue
            url = image.url
            if request is not None:
                url = request.build_absolute_uri(url)
            images.append(url)
        return images


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for a product inside the cart."""

    product = ProductSerializer(read_only=True)
    total_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        coerce_to_string=False,
        read_only=True,
    )

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'total_price')


class CartSerializer(serializers.ModelSerializer):
    """Serializer for the full cart with totals."""

    items = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('items', 'total_items', 'total_price')

    @extend_schema_field(CartItemSerializer(many=True))
    def get_items(self, cart):
        """Return cart items with product details."""
        items = cart.items.select_related(
            'product__subcategory__category',
        ).all()
        return CartItemSerializer(
            items,
            many=True,
            context=self.context,
        ).data

    def get_total_items(self, cart) -> int:
        """Return the total number of products in the cart."""
        return cart.get_total_quantity()

    def get_total_price(self, cart) -> Decimal:
        """Return the total price of the cart."""
        return cart.get_total_price()


class CartItemAddSerializer(serializers.Serializer):
    """Serializer for adding a product to the cart."""

    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
    )
    quantity = serializers.IntegerField(min_value=1, max_value=32767)

    def create(self, validated_data):
        """Add a product or increase its quantity."""
        cart = self.context['cart']
        product = validated_data['product']
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': validated_data['quantity']},
        )
        if not created:
            item.quantity += validated_data['quantity']
            item.save(update_fields=('quantity',))
        self.created = created
        return item


class CartItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for changing the quantity of a cart item."""

    quantity = serializers.IntegerField(min_value=1, max_value=32767)

    class Meta:
        model = CartItem
        fields = ('quantity',)
