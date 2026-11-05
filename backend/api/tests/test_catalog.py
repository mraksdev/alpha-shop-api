"""Tests for the public catalog API."""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.tests.base import MediaMixin, make_image_file
from catalog.models import Category, Product, Subcategory


class CatalogApiTests(MediaMixin, APITestCase):
    """Check GET endpoints of categories and products."""

    @classmethod
    def setUpTestData(cls):
        cls.electronics = Category.objects.create(
            name='Electronics',
            slug='electronics',
            image=make_image_file('electronics.jpg'),
        )
        cls.home = Category.objects.create(
            name='Home',
            slug='home',
            image=make_image_file('home.jpg'),
        )
        cls.smartphones = Subcategory.objects.create(
            category=cls.electronics,
            name='Smartphones',
            slug='smartphones',
            image=make_image_file('smartphones.jpg'),
        )
        cls.kitchen = Subcategory.objects.create(
            category=cls.home,
            name='Kitchen',
            slug='kitchen',
            image=make_image_file('kitchen.jpg'),
        )
        cls.phone = Product.objects.create(
            subcategory=cls.smartphones,
            name='Alpha Phone',
            slug='alpha-phone',
            price=Decimal('999.90'),
            image=make_image_file('phone.jpg'),
        )
        cls.blender = Product.objects.create(
            subcategory=cls.kitchen,
            name='Alpha Blender',
            slug='alpha-blender',
            price=Decimal('49.50'),
            image=make_image_file('blender.jpg'),
        )

    def test_category_list_returns_paginated_categories(self):
        """Categories are returned with their subcategories."""
        response = self.client.get(reverse('categories-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        electronics = next(
            item
            for item in response.data['results']
            if item['slug'] == 'electronics'
        )
        self.assertEqual(len(electronics['subcategories']), 1)
        self.assertEqual(
            electronics['subcategories'][0]['slug'],
            'smartphones',
        )

    def test_category_detail_uses_slug(self):
        """A category can be fetched by its slug."""
        response = self.client.get(
            reverse('categories-detail', args=(self.home.slug,)),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Home')

    def test_product_list_returns_products_with_images(self):
        """Products expose category, subcategory, price and images."""
        response = self.client.get(reverse('products-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        product = next(
            item
            for item in response.data['results']
            if item['slug'] == 'alpha-phone'
        )
        self.assertEqual(product['price'], Decimal('999.90'))
        self.assertEqual(product['category']['slug'], 'electronics')
        self.assertEqual(product['subcategory']['slug'], 'smartphones')
        self.assertEqual(len(product['images']), 3)
        for image_url in product['images']:
            self.assertTrue(image_url.startswith('http://testserver/media/'))

    def test_product_list_can_be_filtered(self):
        """Products can be filtered by category and subcategory slugs."""
        by_category = self.client.get(
            reverse('products-list'),
            {'category': 'home'},
        )
        by_subcategory = self.client.get(
            reverse('products-list'),
            {'subcategory': 'smartphones'},
        )

        self.assertEqual(by_category.status_code, status.HTTP_200_OK)
        self.assertEqual(by_category.data['count'], 1)
        self.assertEqual(
            by_category.data['results'][0]['slug'],
            'alpha-blender',
        )
        self.assertEqual(by_subcategory.status_code, status.HTTP_200_OK)
        self.assertEqual(by_subcategory.data['count'], 1)
        self.assertEqual(
            by_subcategory.data['results'][0]['slug'],
            'alpha-phone',
        )

    def test_product_detail_uses_slug(self):
        """A product can be fetched by its slug."""
        response = self.client.get(
            reverse('products-detail', args=(self.phone.slug,)),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Alpha Phone')

    def test_product_list_is_paginated(self):
        """The product list contains no more than ten products per page."""
        Product.objects.bulk_create([
            Product(
                subcategory=self.smartphones,
                name='Extra product {}'.format(index),
                slug='extra-product-{}'.format(index),
                price=Decimal('10.00'),
            )
            for index in range(11)
        ])

        first_page = self.client.get(reverse('products-list'))
        second_page = self.client.get(reverse('products-list'), {'page': 2})

        self.assertEqual(first_page.status_code, status.HTTP_200_OK)
        self.assertEqual(first_page.data['count'], 13)
        self.assertEqual(len(first_page.data['results']), 10)
        self.assertIsNotNone(first_page.data['next'])
        self.assertEqual(second_page.status_code, status.HTTP_200_OK)
        self.assertEqual(len(second_page.data['results']), 3)
