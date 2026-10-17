from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    """Tests for the member login and logout authentication flows."""

    def setUp(self):
        self.username = "testmember"
        self.password = "StrongPass123!"
        self.user = User.objects.create_user(
            username=self.username,
            email="member@example.com",
            password=self.password,
        )
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.dashboard_url = reverse("dashboard")

    def test_login_page_renders_successfully(self):
        """Verify the login page returns 200 and uses the login template."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(response, "Member Sign In")
        self.assertContains(response, "Invite-Only Access")

    def test_valid_login_redirects_to_dashboard(self):
        """Verify valid credentials authenticate and redirect to /dashboard/."""
        response = self.client.post(
            self.login_url,
            {"username": self.username, "password": self.password},
            follow=True,
        )
        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(response.context["user"].is_authenticated)
        self.assertEqual(response.context["user"].username, self.username)

    def test_valid_login_with_next_param_redirects_to_target(self):
        """Verify the 'next' query parameter is respected after login."""
        target_url = "/dashboard/"
        url_with_next = f"{self.login_url}?next={target_url}"
        response = self.client.post(
            url_with_next,
            {"username": self.username, "password": self.password},
            follow=True,
        )
        self.assertRedirects(response, target_url)

    def test_invalid_login_fails_and_displays_error(self):
        """Verify incorrect credentials stay on login page with an error."""
        response = self.client.post(
            self.login_url,
            {"username": self.username, "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertTrue(response.context["form"].errors)

    def test_authenticated_user_accessing_login_page_is_redirected(self):
        """Verify an already authenticated user is redirected to the dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertRedirects(response, self.dashboard_url)

    def test_logout_redirects_to_home(self):
        """Verify logging out clears the session and redirects to the home page."""
        self.client.force_login(self.user)
        response = self.client.post(self.logout_url, follow=True)
        self.assertRedirects(response, reverse("home"))
        self.assertFalse(response.context["user"].is_authenticated)


class ProtectedPageExampleTests(TestCase):
    """
    REFERENCE PATTERN: Example test suite verifying that a page is protected by authentication.
    
    You can copy and adapt this pattern for any new view or page added to GROW:
    1. Verify unauthenticated requests redirect (302) to the login URL with ?next=<url>.
    2. Verify authenticated requests return status 200 and the expected template.
    """

    def setUp(self):
        self.member = User.objects.create_user(
            username="gym_user",
            password="gym_password_123",
        )
        # Target protected route: The member dashboard
        self.protected_url = reverse("dashboard")
        self.login_url = reverse("login")

    def test_unauthenticated_access_is_redirected_to_login(self):
        """
        GIVEN an unauthenticated client
        WHEN requesting a protected page
        THEN the client must receive a 302 redirect to the login page with ?next=<protected_url>.
        """
        response = self.client.get(self.protected_url)
        
        # 1. Assert status code is a redirect (302)
        self.assertEqual(response.status_code, 302)
        
        # 2. Assert redirect points to login with next parameter
        expected_redirect_url = f"{self.login_url}?next={self.protected_url}"
        self.assertRedirects(response, expected_redirect_url)

    def test_authenticated_access_is_allowed(self):
        """
        GIVEN an authenticated member
        WHEN requesting a protected page
        THEN the page must render successfully with status 200 and the correct template.
        """
        # Authenticate the test client
        self.client.force_login(self.member)

        response = self.client.get(self.protected_url)

        # 1. Assert status code is 200 OK
        self.assertEqual(response.status_code, 200)

        # 2. Assert the expected template is used
        self.assertTemplateUsed(response, "dashboard.html")

        # 3. Assert member user context is present
        self.assertEqual(response.context["user"].username, "gym_user")
