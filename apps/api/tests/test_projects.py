"""Tests for GET /api/v1/projects."""
from ._helpers import ApiTestCase


class ProjectListTests(ApiTestCase):
    url = "/api/v1/projects"

    def test_returns_member_projects_with_languages(self):
        """GIVEN the user is a member of one project that has one language configured
        WHEN /projects is called
        THEN the response includes that project with its language list."""
        resp = self.client.get(self.url, **self.auth())
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["projects"]), 1)
        p = data["projects"][0]
        self.assertEqual(p["slug"], self.project.slug)
        self.assertEqual(p["org_slug"], self.org.slug)
        self.assertEqual(len(p["languages"]), 1)
        self.assertEqual(p["languages"][0]["code"], "ru")

    def test_outsider_sees_empty_list(self):
        """GIVEN a user who has no project memberships
        WHEN /projects is called
        THEN the response has an empty list."""
        resp = self.client.get(self.url, **self.auth(self.outsider_token))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"projects": []})

    def test_unauthenticated_returns_401(self):
        """GIVEN no Authorization header
        WHEN /projects is called
        THEN 401 is returned."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)
