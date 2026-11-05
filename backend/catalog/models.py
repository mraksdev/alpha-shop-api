import io
import uuid
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import models
from PIL import Image

MEDIUM_IMAGE_SIZE = (800, 800)
SMALL_IMAGE_SIZE = (300, 300)


class ResizedProductImageMixin:
    """Generate medium and small product images on save."""

    RESIZED_IMAGES = {
        'image_medium': MEDIUM_IMAGE_SIZE,
        'image_small': SMALL_IMAGE_SIZE,
    }

    def __init__(self, *args, **kwargs):
        """Remember the original image name to detect replacements."""
        super().__init__(*args, **kwargs)
        self._original_image_name = self.image.name if self.image else None

    def save(self, *args, **kwargs):
        """Create resized copies when the original image changes."""
        image_changed = (
            self.image
            and self.image.name != self._original_image_name
        )
        if image_changed or not self.image_medium or not self.image_small:
            self._generate_resized_images()
        super().save(*args, **kwargs)
        self._original_image_name = self.image.name if self.image else None

    def _generate_resized_images(self) -> None:
        """Create medium and small copies of the uploaded image."""
        if not self.image:
            return
        for field_name in self.RESIZED_IMAGES:
            field_file = getattr(self, field_name)
            if field_file:
                field_file.delete(save=False)
        with Image.open(self.image) as source:
            image_format = source.format or 'JPEG'
            image = source.copy()
        if image_format == 'JPEG':
            image = image.convert('RGB')
        extension = Path(self.image.name).suffix.lower().lstrip('.') or 'jpg'
        for field_name, size in self.RESIZED_IMAGES.items():
            resized = image.copy()
            resized.thumbnail(size, Image.LANCZOS)
            buffer = io.BytesIO()
            resized.save(buffer, format=image_format)
            getattr(self, field_name).save(
                '{}.{}'.format(uuid.uuid4(), extension),
                ContentFile(buffer.getvalue()),
                save=False,
            )


class Category(models.Model):
    """Product category."""

    name = models.CharField(
        'наименование',
        max_length=200,
        unique=True,
    )
    slug = models.SlugField('slug-имя', max_length=200, unique=True)
    image = models.ImageField('изображение', upload_to='categories/')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name


class Subcategory(models.Model):
    """Subcategory that belongs to a parent category."""

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subcategories',
        verbose_name='категория',
    )
    name = models.CharField('наименование', max_length=200)
    slug = models.SlugField('slug-имя', max_length=200, unique=True)
    image = models.ImageField('изображение', upload_to='subcategories/')

    class Meta:
        verbose_name = 'подкатегория'
        verbose_name_plural = 'подкатегории'
        ordering = ('name',)

    def __str__(self) -> str:
        return '{}: {}'.format(self.category.name, self.name)


class Product(ResizedProductImageMixin, models.Model):
    """Product from the catalog."""

    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='подкатегория',
    )
    name = models.CharField('наименование', max_length=200)
    slug = models.SlugField('slug-имя', max_length=200, unique=True)
    price = models.DecimalField(
        'цена',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    image = models.ImageField('изображение', upload_to='products/')
    image_medium = models.ImageField(
        'среднее изображение',
        upload_to='products/medium/',
        blank=True,
        editable=False,
    )
    image_small = models.ImageField(
        'маленькое изображение',
        upload_to='products/small/',
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'продукты'
        ordering = ('name',)

    def __str__(self) -> str:
        return self.name

    @property
    def category(self):
        """Return the product category through its subcategory."""
        return self.subcategory.category
