from rest_framework import serializers

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

    def get_images(self, product):
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
