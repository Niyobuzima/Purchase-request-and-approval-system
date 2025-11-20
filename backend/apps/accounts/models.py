from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the Purchase Request & Approval System.

    Supports role-based access control with five roles:
    - STAFF: Regular employees who create purchase requests
    - APPROVER_L1: First-level managers who approve requests
    - APPROVER_L2: Senior managers who give final approval
    - FINANCE: Finance team members who handle purchase orders
    - ADMIN: System administrators with full access
    """

    ROLE_CHOICES = [
        ('STAFF', 'Staff'),
        ('APPROVER_L1', 'Approver Level 1'),
        ('APPROVER_L2', 'Approver Level 2'),
        ('FINANCE', 'Finance'),
        ('ADMIN', 'Admin'),
    ]

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the user'
    )

    # Authentication fields
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text='User email address (used for login)'
    )

    # Personal information
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        help_text='Unique employee identifier (format: proc-<number>)'
    )

    # Role and permissions
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STAFF',
        db_index=True,
        help_text='User role determines access level and capabilities'
    )
    approval_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        null=True,
        blank=True,
        help_text='Approval level for APPROVER roles (1 or 2)'
    )

    # Account status
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user should be treated as active'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into the admin site'
    )

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Return the user's full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the user's first name."""
        return self.first_name or self.email

    def is_approver(self):
        """Check if user is an approver (L1 or L2)."""
        return self.role in ['APPROVER_L1', 'APPROVER_L2']

    def can_approve_at_level(self, level):
        """Check if user can approve at the specified level."""
        if self.role == 'APPROVER_L1' and level == 1:
            return True
        if self.role == 'APPROVER_L2' and level == 2:
            return True
        if self.role == 'ADMIN':
            return True
        return False

    def save(self, *args, **kwargs):
        """Override save to set approval_level and employee_id.

        Respects update_fields to avoid conflicts with Django's internal saves.
        """
        update_fields = kwargs.get('update_fields', None)

        # Handle partial updates (when update_fields is specified)
        if update_fields is not None:
            # For partial updates, ensure we don't modify fields that aren't in update_fields
            # Reload the original values from DB to prevent Django from detecting unwanted changes
            if self.pk and ('approval_level' not in update_fields or 'is_staff' not in update_fields):
                # Get current DB values for fields we shouldn't modify
                db_instance = User.objects.filter(pk=self.pk).values('approval_level', 'is_staff').first()
                if db_instance:
                    if 'approval_level' not in update_fields:
                        self.approval_level = db_instance['approval_level']
                    if 'is_staff' not in update_fields:
                        self.is_staff = db_instance['is_staff']
        else:
            # Full save - set approval level based on role
            if self.role == 'APPROVER_L1':
                self.approval_level = 1
            elif self.role == 'APPROVER_L2':
                self.approval_level = 2
            else:
                self.approval_level = None

            # Admins should have staff access
            if self.role == 'ADMIN':
                self.is_staff = True

        # Auto-generate employee_id if not provided (only on full save)
        if not self.employee_id and update_fields is None:
            from django.db import transaction, IntegrityError
            from django.db.models import Max
            from django.db.models.functions import Cast, Replace
            from django.db.models import IntegerField, Value
            import time
            import random

            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    with transaction.atomic():
                        # Use aggregate to get max number efficiently
                        # This prevents race conditions by using database-level operations
                        result = User.objects.filter(
                            employee_id__startswith='proc-'
                        ).aggregate(
                            max_id=Max(
                                Cast(
                                    Replace('employee_id', Value('proc-'), Value('')),
                                    IntegerField()
                                )
                            )
                        )

                        last_number = result['max_id'] or 1000
                        new_number = last_number + 1

                        self.employee_id = f"proc-{new_number}"

                        # Save with transaction protection
                        super().save(*args, **kwargs)
                        break

                except IntegrityError:
                    # If we get a duplicate, retry with exponential backoff
                    if attempt == max_attempts - 1:
                        raise
                    # Exponential backoff with jitter
                    time.sleep(0.1 * (2 ** attempt) + random.uniform(0, 0.1))
        else:
            # Normal save (either employee_id exists or partial field update)
            super().save(*args, **kwargs)
