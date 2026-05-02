"""Tests for GET /api/v1/coverage/suggest."""
from datetime import date, timedelta

from apps.coverage.models import SearchSession
from apps.keywords.models import Keyword

from ._helpers import ApiTestCase


class CoverageSuggestTests(ApiTestCase):
    url = "/api/v1/coverage/suggest"

    def test_returns_top3_with_stalest_first(self):
        """GIVEN a project with one (platform, language, category) cell and an active keyword
        WHEN /suggest is called
        THEN the cell appears in suggestions and includes the example_keyword."""
        Keyword.objects.create(
            organization=self.org,
            project=self.project,
            term="попугай",
            language="ru",
            category=self.cat_parrots,
            status=Keyword.Status.ACTIVE,
        )
        resp = self.client.get(
            f"{self.url}?project_id={self.project.pk}", **self.auth()
        )
        self.assertEqual(resp.status_code, 200)
        suggestions = resp.json()["suggestions"]
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["platform"], "Telegram")
        self.assertEqual(suggestions[0]["language"], "Russian")
        self.assertEqual(suggestions[0]["category"], "Parrots")
        self.assertEqual(suggestions[0]["example_keyword"], "попугай")
        self.assertIn("t.me", suggestions[0]["search_url"])
        # Never-searched cell ranks first → last_searched is null
        self.assertIsNone(suggestions[0]["last_searched"])

    def test_recent_session_pushes_cell_down(self):
        """GIVEN one cell searched today and another never searched
        WHEN /suggest is called
        THEN the never-searched cell ranks before the recently-searched one."""
        from apps.core.models import KeywordCategory, Language, Platform

        # second cell
        platform_vk = Platform.objects.create(project=self.project, name="VK", url_pattern=r"vk\.com")
        cat_other = KeywordCategory.objects.create(project=self.project, name="Snakes", slug="snakes")
        # log a session covering (Telegram, ru, parrots) today
        SearchSession.objects.create(
            project=self.project,
            volunteer=self.user,
            platform=self.platform_telegram,
            language="ru",
            keyword_categories=["parrots"],
            date=date.today(),
        )
        resp = self.client.get(f"{self.url}?project_id={self.project.pk}", **self.auth())
        suggestions = resp.json()["suggestions"]
        # cells: 2 platforms × 1 lang × 2 categories = 4 cells; one was searched today
        # Top suggestion must NOT be (Telegram, ru, parrots)
        first = suggestions[0]
        self.assertFalse(
            first["platform"] == "Telegram" and first["category"] == "Parrots"
        )

    def test_missing_project_id_returns_400(self):
        """GIVEN no project_id query param
        WHEN /suggest is called
        THEN 400 is returned."""
        resp = self.client.get(self.url, **self.auth())
        self.assertEqual(resp.status_code, 400)

    def test_non_member_returns_403(self):
        """GIVEN a token that is not a member of the requested project
        WHEN /suggest is called
        THEN 403 is returned."""
        resp = self.client.get(
            f"{self.url}?project_id={self.project.pk}",
            **self.auth(self.outsider_token),
        )
        self.assertEqual(resp.status_code, 403)
