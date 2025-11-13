"""
Custom allauth adapters for HygGeo
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter that auto-connects Google accounts
    to existing HygGeo accounts when the email matches.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually processed.

        If the user already has an account with the same email address,
        automatically connect the social account to the existing account.
        """
        # If user is already logged in, don't do anything
        if request.user.is_authenticated:
            return

        # If this social account is already connected, continue normally
        if sociallogin.is_existing:
            return

        # Try to find an existing user with the same email
        try:
            email = sociallogin.email_addresses[0].email.lower()

            # Check if a user with this email already exists
            try:
                user = User.objects.get(email__iexact=email)

                # Auto-connect the social account to this user
                sociallogin.connect(request, user)

                # Perform the login
                from django.contrib.auth import login
                from allauth.account.utils import perform_login

                # This will log the user in with the connected account
                perform_login(request, user, email_verification='none')

            except User.DoesNotExist:
                # No user with this email exists, proceed with normal signup
                pass

        except (IndexError, KeyError):
            # No email provided by social provider (shouldn't happen with Google)
            pass

    def populate_user(self, request, sociallogin, data):
        """
        Populate user information from social provider data.
        This is called when creating a new user via social login.
        """
        user = super().populate_user(request, sociallogin, data)

        # Get additional data from Google
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data

            # Set names from Google data
            if not user.first_name and extra_data.get('given_name'):
                user.first_name = extra_data.get('given_name')

            if not user.last_name and extra_data.get('family_name'):
                user.last_name = extra_data.get('family_name')

            # Generate username from email if not set
            if not user.username:
                email = sociallogin.email_addresses[0].email
                base_username = email.split('@')[0]
                username = base_username

                # Make sure username is unique
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user.username = username

        return user

    def save_user(self, request, sociallogin, form=None):
        """
        Saves a new user instance using information provided in the
        social login signup form.
        """
        user = super().save_user(request, sociallogin, form)

        # Create UserProfile if it doesn't exist
        from accounts.models import UserProfile

        if not hasattr(user, 'userprofile'):
            UserProfile.objects.create(
                user=user,
                email_consent=True  # Default to true for social signups
            )

        return user
