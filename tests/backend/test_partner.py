
from copy import deepcopy

import pytest
from django.test import RequestFactory, client
from django.urls import reverse
from django_rest_passwordreset.tokens import get_token_generator
from rest_framework import status

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient, APITestCase, APIRequestFactory, \
    APILiveServerTestCase
from rest_framework.authtoken.models import Token
from backend.models import User, ConfirmEmailToken, ProductInfo
from backend import views


class UserAPITests(APITestCase):
    """ Tests for working with users. """

    url = reverse('backend:user-register')
    login_url = reverse('backend:user-login')
    details_url = reverse('backend:user-details')

    data = {
        'first_name': 'Name1',
        'last_name': 'Name2',
        'email': 'name2@mail.com',
        'password': 'name1name2',
        'company': 'Company1',
        'position': 'Position1',
        'contacts': []
    }

    def setUp(self):
        return super().setUp()

    def create_user(self):
        data = deepcopy(self.data)
        contact = data.pop('contacts', [])
        password = data.pop('password')

        user = User.objects.create(**data, type='buyer')
        user.is_active = True
        user.set_password(password)
        user.save()

    def test_register_user(self):
        """ Checks for new user registrations. """

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.data['email'], 'name2@mail.com')

    def test_create_user_not_field(self):
        """
        Checks for new user registrations,
        if not all fields are specified.
        """

        data = deepcopy(self.data)
        data.pop('email')

        response = self.create_user()

        self.assertEqual(self.failureException, AssertionError)

    def test_create_user_not_valid_field(self):
        """
        Checks for new user registrations,
        field isn't valid.
        """

        data = deepcopy(self.data)
        self.data['email'] = ''

        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Errors', response.data)
        self.assertEqual(response.data['Status'], False)

    def test_create_user_wrong_field(self):
        """
        Checks for new user registrations,
        field is wrong.
        """

        data = deepcopy(self.data)
        self.data.pop('last_name')

        response = self.client.post(self.url, self.data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)
        self.assertEqual(response.data['Status'], False)


    def test_user_login(self):
        """ Checks for login is success. """

        self.create_user()
        email = self.data['email']
        password = self.data['password']
        login_data = dict(email=email, password=password)

        response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Status', response.data)
        self.assertEqual(response.data['Status'], True)


    def test_user_login_not_field(self):
        """
        Checks for login, if not all fields are specified.
        """

        self.create_user()
        email = self.data['email']
        password = self.data['password']
        login_data = dict(email=email, password=password)
        login_data.pop('email')

        response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(self.failureException, AssertionError)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_contact_view(self):
        """ Get user contacts. """

        url_contact = reverse('backend:user-contact')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(url_contact, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('Errors', response.data)


    def test_get_contact_view_not_authorize(self):
        """ Get user contacts without authorization. """

        url_contact = reverse('backend:user-contact')

        response = self.client.get(url_contact, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Error', response.data)
        self.assertEqual(response.data['Status'], False)

    def test_post_contact_view(self):
        """ Create user's contacts. """

        url_contact = reverse('backend:user-contact')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {
                "city": "Moscow",
                "street": "Lenina",
                "house": "20",
                "structure": "3",
                "building": "0",
                "apartment": "0",
                "phone": "85-58-87"
                }

        response = self.client.post(url_contact, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('Error', response.data)
        self.assertEqual(response.data['Status'], True)

    def test_post_contact_view_not_field(self):
        """ Create user's contacts, if not all fields are specified. """

        url_contact = reverse('backend:user-contact')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {
                "city": "Moscow",
                "structure": "3",
                "building": "0",
                "apartment": "0",
                "phone": "85-58-87"
                }

        response = self.client.post(url_contact, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)
        self.assertEqual(response.data['Status'], False)

    def test_del_contact_view(self):
        """ Delete user contact. """

        url_contact = reverse('backend:user-contact')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {"items": "6"}

        response = self.client.delete(url_contact, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['Status'], True)

    def test_del_contact_view_not_fields(self):
        """ Delete user contact, if not all fields are specified. """

        url_contact = reverse('backend:user-contact')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {"items": ''}

        response = self.client.delete(url_contact, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['Status'], False)


class PartnerAPITests(APITestCase):
    """ Tests for working with orders. """

    data = {
        'first_name': 'Name1',
        'last_name': 'Name2',
        'email': 'name2@mail.com',
        'password': 'name1name2',
        'company': 'Company1',
        'position': 'Position1',
        'contacts': []
    }

    def setUp(self):
        return super().setUp()

    def create_user(self):
        data = deepcopy(self.data)
        contact = data.pop('contacts', [])
        password = data.pop('password')

        user = User.objects.create(**data, type='shop')
        user.is_active = True
        user.set_password(password)
        user.save()

    def test_get_basket_view(self):
        """ Get basket. """

        url_basket = reverse('backend:basket')
        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(url_basket, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('Errors', response.data)

    def test_delete_basket_view(self):
        """ Delete basket. """

        url_contact = reverse('backend:basket')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {"items": "6"}

        response = self.client.delete(url_contact, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['Status'], True)

    def test_get_partner_orders(self):
        """ Get partner orders. """

        url_orders = reverse('backend:partner-orders')
        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {"url":
                "https://raw.githubusercontent.com/netology-code/pd-diplom/"
                "master/data/shop1.yaml"}

        response = self.client.get(url_orders, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_partner_orders_not_authorize(self):
        """ Get partner orders without authorization. """

        url_orders = reverse('backend:partner-orders')

        data = {"url":
                "https://raw.githubusercontent.com/netology-code/pd-diplom/"
                "master/data/shop1.yaml"}

        response = self.client.get(url_orders, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Error', response.data)
        self.assertEqual(response.data['Status'], False)

    def test_get_order_view(self):
        """ Get orders. """

        url_order = reverse('backend:order')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        response = self.client.get(url_order, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_order_view_not_authorize(self):
        """ Get orders without authorization. """

        url_order = reverse('backend:order')

        response = self.client.get(url_order, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Error', response.data)
        self.assertEqual(response.data['Status'], False)

    def test_post_order_view(self):
        """ Create order. """

        url_order = reverse('backend:order')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {
                "id": "4",
                "contact": "8"
                }

        response = self.client.post(url_order, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_order_view_not_authorize(self):
        """ Create order without authorization. """

        url_order = reverse('backend:order')

        data = {
                "id": "4",
                "contact": "8"
                }

        response = self.client.post(url_order, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Error', response.data)
        self.assertEqual(response.data['Status'], False)

    def test_post_order_view_not_field(self):
        """ Create order, if not all fields are specified. """

        url_order = reverse('backend:order')

        self.create_user()
        email = self.data['email']
        user = User.objects.get(email=email)
        token = Token.objects.get_or_create(user_id=user.id)[0].key
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {
                "id": "4"
                }

        response = self.client.post(url_order, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Errors', response.data)
        self.assertEqual(response.data['Status'], False)














