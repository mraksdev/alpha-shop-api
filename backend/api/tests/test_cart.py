"""Tests for the authenticated cart API."""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from api.tests.base import MediaMixin, make_image_file
from cart.models import Cart, CartItem
from catalog.models import Category, Product, Subcategory
from users.models import User


class CartApiTests(MediaMixin, APITestCase):
    """Check GET, POST, PATCH and DELETE cart endpoints."""

    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(
            name='Cart category',
            slug='cart-category',
            image=make_image_file('category.jpg'),
        )
        subcategory = Subcategory.objects.create(
            category=category,
            name='Cart subcategory',
            slug='cart-subcategory',
            image=make_image_file('subcategory.jpg'),
        )
        cls.first_product = Product.objects.create(
            subcategory=subcategory,
            name='First product',
            slug='first-product',
            price=Decimal('99.90'),
            image=make_image_file('first.jpg'),
        )
        cls.second_product = Product.objects.create(
            subcategory=subcategory,
            name='Second product',
            slug='second-product',
            price=Decimal('10.50'),
            image=make_image_file('second.jpg'),
        )

    def setUp(self):
        self.user = User.objects.create_user(
            email='customer@example.com',
            username='customer',
            password='StrongPass123',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token {}'.format(self.token.key),
        )

    def add_to_cart(self, product, quantity=1):
        """Send a POST request that adds a product to the cart."""
        return self.client.post(
            reverse('cart-items'),
            {'product': product.id, 'quantity': quantity},
            format='json',
        )

    def test_cart_requires_authentication(self):
        """Anonymous users cannot read or change the cart."""
        anonymous = APIClient()

        self.assertEqual(
            anonymous.get(reverse('cart')).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            anonymous.post(
                reverse('cart-items'),
                {'product': self.first_product.id, 'quantity': 1},
                format='json',
            ).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_add_product_to_cart(self):
        """A new product is added with the requested quantity."""
        response = self.add_to_cart(self.first_product, quantity=2)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 2)
        self.assertEqual(
            response.data['total_price'],
            Decimal('199.80'),
        )
        self.assertEqual(
            response.data['product']['slug'],
            'first-product',
        )
        self.assertEqual(
            Cart.objects.get(user=self.user).get_total_quantity(),
            2,
        )

    def test_repeated_add_increases_quantity(self):
        """Adding the same product twice increases its quantity."""
        self.add_to_cart(self.first_product, quantity=2)

        response = self.add_to_cart(self.first_product, quantity=3)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 5)
        self.assertEqual(
            CartItem.objects.filter(cart__user=self.user).count(),
            1,
        )

    def test_add_rejects_invalid_data(self):
        """Invalid products and quantities are rejected."""
        invalid_quantity = self.add_to_cart(self.first_product, quantity=0)
        too_large = self.add_to_cart(self.first_product, quantity=32768)
        unknown_product = self.client.post(
            reverse('cart-items'),
            {'product': 999999, 'quantity': 1},
            format='json',
        )

        self.assertEqual(
            invalid_quantity.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(too_large.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            unknown_product.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_get_cart_returns_totals(self):
        """The cart response contains items, quantity and total price."""
        self.add_to_cart(self.first_product, quantity=2)
        self.add_to_cart(self.second_product, quantity=1)

        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 3)
        self.assertEqual(response.data['total_price'], Decimal('210.30'))
        self.assertEqual(len(response.data['items']), 2)

    def test_update_cart_item_quantity(self):
        """A cart item quantity can be changed with PATCH."""
        self.add_to_cart(self.first_product, quantity=1)

        response = self.client.patch(
            reverse('cart-item-detail', args=(self.first_product.id,)),
            {'quantity': 4},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['quantity'], 4)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.get_total_quantity(), 4)
        self.assertEqual(cart.get_total_price(), Decimal('399.60'))

    def test_update_rejects_invalid_quantity(self):
        """The quantity of a cart item must be positive."""
        self.add_to_cart(self.first_product, quantity=1)

        response = self.client.patch(
            reverse('cart-item-detail', args=(self.first_product.id,)),
            {'quantity': 0},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_cart_item(self):
        """A product can be removed from the cart."""
        self.add_to_cart(self.first_product, quantity=2)
        self.add_to_cart(self.second_product, quantity=1)

        response = self.client.delete(
            reverse('cart-item-detail', args=(self.first_product.id,)),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.get_total_quantity(), 1)
        self.assertEqual(cart.get_total_price(), Decimal('10.50'))

    def test_clear_cart(self):
        """DELETE /api/cart/ removes every item from the cart."""
        self.add_to_cart(self.first_product, quantity=2)
        self.add_to_cart(self.second_product, quantity=1)

        response = self.client.delete(reverse('cart'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(
            CartItem.objects.filter(cart__user=self.user).count(),
            0,
        )

    def test_user_cannot_change_another_users_cart(self):
        """Cart items of other users are not accessible."""
        self.add_to_cart(self.first_product, quantity=2)
        other_user = User.objects.create_user(
            email='other@example.com',
            username='other',
            password='StrongPass123',
        )
        other_token = Token.objects.create(user=other_user)
        other_client = APIClient()
        other_client.credentials(
            HTTP_AUTHORIZATION='Token {}'.format(other_token.key),
        )

        update_response = other_client.patch(
            reverse('cart-item-detail', args=(self.first_product.id,)),
            {'quantity': 1},
            format='json',
        )
        delete_response = other_client.delete(
            reverse('cart-item-detail', args=(self.first_product.id,)),
        )
        other_cart = other_client.get(reverse('cart'))

        self.assertEqual(
            update_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            delete_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(other_cart.data['total_items'], 0)
        self.assertEqual(
            Cart.objects.get(user=self.user).get_total_quantity(),
            2,
        )
