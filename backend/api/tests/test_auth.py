"""Tests for registration and token authentication endpoints."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class AuthApiTests(APITestCase):
    """Check POST registration, login, logout and GET current user."""

    registration_data = {
        'username': 'newuser',
        'first_name': 'New',
        'last_name': 'User',
        'email': 'newuser@example.com',
        'password': 'StrongPass123',
    }

    def test_register_user(self):
        """A new user can be created through the API."""
        response = self.client.post(
            '/api/auth/users/',
            self.registration_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'newuser@example.com')
        self.assertTrue(
            User.objects.filter(email='newuser@example.com').exists(),
        )

    def test_register_rejects_duplicate_email(self):
        """The email field is unique."""
        User.objects.create_user(
            email='newuser@example.com',
            username='existing',
            password='StrongPass123',
        )

        response = self.client.post(
            '/api/auth/users/',
            self.registration_data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_token(self):
        """Token authentication accepts email and password."""
        User.objects.create_user(
            email='login@example.com',
            username='loginuser',
            password='StrongPass123',
        )

        response = self.client.post(
            '/api/auth/token/login/',
            {'email': 'login@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('auth_token', response.data)

    def test_login_rejects_wrong_password(self):
        """Invalid credentials do not return a token."""
        User.objects.create_user(
            email='login@example.com',
            username='loginuser',
            password='StrongPass123',
        )

        response = self.client.post(
            '/api/auth/token/login/',
            {'email': 'login@example.com', 'password': 'wrong-password'},
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_current_user_requires_token(self):
        """The current user endpoint is unavailable without a token."""
        response = self.client.get('/api/auth/users/me/')

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_and_logout(self):
        """A token exposes the current user and can be revoked."""
        user = User.objects.create_user(
            email='login@example.com',
            username='loginuser',
            password='StrongPass123',
        )
        token_response = self.client.post(
            reverse('login'),
            {'email': user.email, 'password': 'StrongPass123'},
            format='json',
        )
        token = token_response.data['auth_token']
        self.client.credentials(
            HTTP_AUTHORIZATION='Token {}'.format(token),
        )

        me_response = self.client.get('/api/auth/users/me/')
        logout_response = self.client.post('/api/auth/token/logout/')
        after_logout = self.client.get('/api/auth/users/me/')

        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['email'], user.email)
        self.assertEqual(
            logout_response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertEqual(
            after_logout.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
