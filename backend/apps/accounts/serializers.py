from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (read operations)."""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'phone',
            'department',
            'employee_id',
            'role',
            'approval_level',
            'is_active',
            'date_joined',
            'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'approval_level']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users via public registration.

    Security: Role is not exposed in registration to prevent privilege escalation.
    All new users are created with the default 'STAFF' role.
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone',
            'department'
        ]

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        """Create user with hashed password and default STAFF role.

        Security: Force role to STAFF regardless of any input.
        Admins must manually upgrade user roles after creation.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Force role to STAFF for security
        validated_data['role'] = 'STAFF'

        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'phone',
            'department',
            'employee_id',
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_old_password(self, value):
        """Verify the old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate(self, attrs):
        """Validate that new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return attrs

    def save(self):
        """Update the user's password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes user information."""

    @classmethod
    def get_token(cls, user):
        """Add custom claims to token."""
        token = super().get_token(user)

        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.get_full_name()

        return token

    def validate(self, attrs):
        """Validate and return token with user data."""
        data = super().validate(attrs)

        # Add user information to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'full_name': self.user.get_full_name(),
            'role': self.user.role,
            'approval_level': self.user.approval_level,
        }

        return data


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for admin to update user roles."""

    class Meta:
        model = User
        fields = ['role', 'is_active']

    def validate_role(self, value):
        """Validate role changes."""
        user = self.instance
        request_user = self.context['request'].user

        # Only admins can change roles
        if not request_user.role == 'ADMIN':
            raise serializers.ValidationError(
                'Only administrators can change user roles.'
            )

        # Prevent users from changing their own role
        if user == request_user:
            raise serializers.ValidationError(
                'You cannot change your own role.'
            )

        return value
