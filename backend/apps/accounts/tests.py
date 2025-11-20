from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model."""

    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'STAFF',
        }

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertEqual(user.role, 'STAFF')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
        self.assertEqual(admin.role, 'ADMIN')

    def test_user_string_representation(self):
        """Test the string representation of user."""
        user = User.objects.create_user(**self.user_data)
        expected = f"Test User (test@example.com)"
        self.assertEqual(str(user), expected)

    def test_get_full_name(self):
        """Test getting user's full name."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'Test User')

    def test_approver_l1_approval_level(self):
        """Test that APPROVER_L1 gets approval_level 1."""
        user = User.objects.create_user(
            email='approver1@example.com',
            password='pass123',
            first_name='Approver',
            last_name='One',
            role='APPROVER_L1'
        )
        self.assertEqual(user.approval_level, 1)

    def test_approver_l2_approval_level(self):
        """Test that APPROVER_L2 gets approval_level 2."""
        user = User.objects.create_user(
            email='approver2@example.com',
            password='pass123',
            first_name='Approver',
            last_name='Two',
            role='APPROVER_L2'
        )
        self.assertEqual(user.approval_level, 2)

    def test_is_approver_method(self):
        """Test is_approver method."""
        approver = User.objects.create_user(
            email='approver@example.com',
            password='pass123',
            first_name='Approver',
            last_name='User',
            role='APPROVER_L1'
        )
        staff = User.objects.create_user(**self.user_data)

        self.assertTrue(approver.is_approver())
        self.assertFalse(staff.is_approver())

    def test_can_approve_at_level(self):
        """Test can_approve_at_level method."""
        approver1 = User.objects.create_user(
            email='approver1@example.com',
            password='pass123',
            first_name='Approver',
            last_name='One',
            role='APPROVER_L1'
        )
        approver2 = User.objects.create_user(
            email='approver2@example.com',
            password='pass123',
            first_name='Approver',
            last_name='Two',
            role='APPROVER_L2'
        )

        self.assertTrue(approver1.can_approve_at_level(1))
        self.assertFalse(approver1.can_approve_at_level(2))
        self.assertFalse(approver2.can_approve_at_level(1))
        self.assertTrue(approver2.can_approve_at_level(2))


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.logout_url = '/api/auth/logout/'
        self.profile_url = '/api/auth/profile/'

        self.user_data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'STAFF',
        }

    def test_user_registration(self):
        """Test user registration."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().email, self.user_data['email'])

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        data = self.user_data.copy()
        data['password_confirm'] = 'DifferentPassword123!'
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name='Existing',
            last_name='User'
        )
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        """Test user login."""
        User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )

        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout(self):
        """Test user logout."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )

        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        logout_data = {'refresh': str(refresh)}
        response = self.client.post(self.logout_url, logout_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_get_user_profile(self):
        """Test getting user profile."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], user.email)
        self.assertEqual(response.data['first_name'], user.first_name)

    def test_update_user_profile(self):
        """Test updating user profile."""
        user = User.objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            first_name=self.user_data['first_name'],
            last_name=self.user_data['last_name']
        )

        self.client.force_authenticate(user=user)
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone': '+250788123456'
        }
        response = self.client.patch(self.profile_url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.phone, '+250788123456')

    def test_profile_requires_authentication(self):
        """Test that profile endpoint requires authentication."""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PermissionTest(APITestCase):
    """Test cases for role-based permissions."""

    def setUp(self):
        """Set up test users with different roles."""
        self.client = APIClient()

        self.staff_user = User.objects.create_user(
            email='staff@example.com',
            password='pass123',
            first_name='Staff',
            last_name='User',
            role='STAFF'
        )

        self.approver_l1 = User.objects.create_user(
            email='approver1@example.com',
            password='pass123',
            first_name='Approver',
            last_name='L1',
            role='APPROVER_L1'
        )

        self.approver_l2 = User.objects.create_user(
            email='approver2@example.com',
            password='pass123',
            first_name='Approver',
            last_name='L2',
            role='APPROVER_L2'
        )

        self.finance_user = User.objects.create_user(
            email='finance@example.com',
            password='pass123',
            first_name='Finance',
            last_name='User',
            role='FINANCE'
        )

        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='pass123',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )

    def test_staff_cannot_access_admin_endpoints(self):
        """Test that staff users cannot access admin endpoints."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_admin_endpoints(self):
        """Test that admin users can access admin endpoints."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_users_by_role_endpoint(self):
        """Test filtering users by role."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/auth/users/by-role/?role=APPROVER_L1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'approver1@example.com')


class ChangePasswordTest(APITestCase):
    """Test cases for password change functionality."""

    def setUp(self):
        """Set up test user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='OldPass123!',
            first_name='Test',
            last_name='User'
        )
        self.change_password_url = '/api/auth/change-password/'

    def test_change_password_success(self):
        """Test successful password change."""
        self.client.force_authenticate(user=self.user)

        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = self.client.post(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_wrong_old_password(self):
        """Test password change with wrong old password."""
        self.client.force_authenticate(user=self.user)

        data = {
            'old_password': 'WrongPassword',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'NewPass123!'
        }
        response = self.client.post(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_mismatch(self):
        """Test password change with mismatched new passwords."""
        self.client.force_authenticate(user=self.user)

        data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewPass123!',
            'new_password_confirm': 'DifferentPass123!'
        }
        response = self.client.post(self.change_password_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
