"""Shared test fixtures for /api/v1/ endpoint tests."""
from django.test import TestCase

from apps.core.models import (
    APIToken,
    KeywordCategory,
    Language,
    Organization,
    OrganizationMembership,
    Platform,
    Project,
    ProjectMembership,
    User,
)


class ApiTestCase(TestCase):
    """Base case providing an org, project, member user, and bearer token."""

    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="ICF", slug="icf")
        cls.project = Project.objects.create(
            organization=cls.org, name="Bird Trade CA", slug="bird-trade-ca"
        )
        cls.user = User.objects.create_user(
            email="vol@crane.local", password="x"
        )
        OrganizationMembership.objects.create(
            user=cls.user,
            organization=cls.org,
            role=OrganizationMembership.Role.MEMBER,
        )
        ProjectMembership.objects.create(
            user=cls.user,
            project=cls.project,
            role=ProjectMembership.Role.VOLUNTEER,
        )
        cls.token = APIToken.objects.create(user=cls.user)

        cls.outsider = User.objects.create_user(
            email="outsider@crane.local", password="x"
        )
        cls.outsider_token = APIToken.objects.create(user=cls.outsider)

        cls.platform_telegram = Platform.objects.create(
            project=cls.project, name="Telegram", url_pattern=r"t\.me"
        )
        cls.lang_ru = Language.objects.create(project=cls.project, name="Russian", code="ru")
        cls.cat_parrots = KeywordCategory.objects.create(
            project=cls.project, name="Parrots", slug="parrots"
        )

    def auth(self, token=None):
        return {"HTTP_AUTHORIZATION": f"Bearer {(token or self.token).key}"}
