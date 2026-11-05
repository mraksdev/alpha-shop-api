from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Category, Product, Subcategory


def image_preview(image, max_height=80):
    """Return an HTML preview of an image."""
    if not image:
        return '—'
    return format_html(
        '<img src="{}" style="max-height: {}px; max-width: 160px;" />',
        image.url,
        max_height,
    )


class SubcategoryInline(admin.TabularInline):
    """Inline editor for subcategories of a category."""

    model = Subcategory
    extra = 1
    fields = ('name', 'slug', 'image', 'preview')
    readonly_fields = ('preview',)

    @admin.display(description='изображение')
    def preview(self, obj):
        """Return a small subcategory image preview."""
        return image_preview(obj.image, 60)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin panel for categories."""

    list_display = (
        'id',
        'name',
        'slug',
        'image_preview',
        'subcategories_count',
    )
    search_fields = ('name', 'slug')
    inlines = (SubcategoryInline,)

    def get_queryset(self, request):
        """Annotate categories with the number of subcategories."""
        return super().get_queryset(request).annotate(
            subcategories_count=Count('subcategories'),
        )

    @admin.display(description='изображение')
    def image_preview(self, obj):
        """Return a category image preview."""
        return image_preview(obj.image)

    @admin.display(description='подкатегорий')
    def subcategories_count(self, obj):
        """Return the number of subcategories."""
        return obj.subcategories_count


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    """Admin panel for subcategories."""

    list_display = (
        'id',
        'name',
        'slug',
        'category',
        'image_preview',
    )
    list_filter = ('category',)
    search_fields = ('name', 'slug')
    list_select_related = ('category',)

    @admin.display(description='изображение')
    def image_preview(self, obj):
        """Return a subcategory image preview."""
        return image_preview(obj.image)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin panel for products."""

    list_display = (
        'id',
        'name',
        'slug',
        'category',
        'subcategory',
        'price',
        'image_preview',
    )
    list_filter = ('subcategory__category', 'subcategory')
    search_fields = ('name', 'slug')
    list_select_related = ('subcategory__category',)
    fields = (
        'name',
        'slug',
        'subcategory',
        'price',
        'image',
        'image_preview',
        'image_medium_preview',
        'image_small_preview',
    )
    readonly_fields = (
        'image_preview',
        'image_medium_preview',
        'image_small_preview',
    )

    @admin.display(description='категория')
    def category(self, obj):
        """Return the product category."""
        return obj.category

    @admin.display(description='изображение')
    def image_preview(self, obj):
        """Return the original image preview."""
        return image_preview(obj.image)

    @admin.display(description='среднее изображение')
    def image_medium_preview(self, obj):
        """Return the medium image preview."""
        return image_preview(obj.image_medium, 120)

    @admin.display(description='маленькое изображение')
    def image_small_preview(self, obj):
        """Return the small image preview."""
        return image_preview(obj.image_small, 80)
