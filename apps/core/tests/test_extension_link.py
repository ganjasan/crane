"""Tests for /auth/extension-link/."""
from django.test import TestCase
from django.urls import reverse

from apps.core.models import APIToken, User


VALID_EXT_ID = "a" * 32  # 32 lowercase chars in [a-p] — Chrome extension ID format


class ExtensionLinkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email="vol@crane.local", password="x")

    def url(self, ext_id=VALID_EXT_ID):
        return reverse("extension_link") + f"?ext_id={ext_id}"

    def test_authenticated_redirect_with_token(self):
        """GIVEN a logged-in user
        WHEN /auth/extension-link/?ext_id=<valid> is requested
        THEN the response is a 302 redirect to the chromiumapp.org URL with the new token."""
        self.client.login(email="vol@crane.local", password="x")
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, 302)
        self.assertIn(f"{VALID_EXT_ID}.chromiumapp.org", resp["Location"])
        self.assertIn("token=", resp["Location"])
        self.assertIn("email=vol%40crane.local", resp["Location"])

        # token in DB matches what was redirected
        token = APIToken.objects.get(user=self.user)
        self.assertIn(f"token={token.key}", resp["Location"])

    def test_unauthenticated_redirects_to_login(self):
        """GIVEN no logged-in user
        WHEN /auth/extension-link/ is requested
        THEN the response is a 302 to /auth/login/."""
        resp = self.client.get(self.url())
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/auth/login/", resp["Location"])

    def test_invalid_ext_id_returns_400(self):
        """GIVEN ext_id with wrong length or chars
        WHEN /auth/extension-link/ is requested
        THEN response is 400."""
        self.client.login(email="vol@crane.local", password="x")
        for bad in ["", "short", "z" * 32, "a" * 31, "Ab" * 16, "1" * 32]:
            with self.subTest(bad=bad):
                resp = self.client.get(reverse("extension_link") + f"?ext_id={bad}")
                self.assertEqual(resp.status_code, 400)

    def test_token_rotates_on_each_call(self):
        """GIVEN a user with an existing APIToken
        WHEN /auth/extension-link/ is called a second time
        THEN the previous token is replaced with a new key."""
        self.client.login(email="vol@crane.local", password="x")
        first = self.client.get(self.url())
        old_token = APIToken.objects.get(user=self.user).key

        second = self.client.get(self.url())
        new_token = APIToken.objects.get(user=self.user).key

        self.assertNotEqual(old_token, new_token)
        self.assertIn(f"token={new_token}", second["Location"])
