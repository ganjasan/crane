"""Tests for POST /api/v1/incidents/check."""
import json

from django.urls import reverse

from apps.incidents.models import Incident

from ._helpers import ApiTestCase


class IncidentCheckTests(ApiTestCase):
    url = "/api/v1/incidents/check"

    def setUp(self):
        super().setUp()
        Incident.objects.create(
            project=self.project,
            organization=self.org,
            url="https://t.me/channel/123?utm_source=email",
        )

    def test_duplicate_detected_via_normalized_url(self):
        """GIVEN an incident saved with utm_* in its URL
        WHEN /check is called with the same URL but a different tracking param
        THEN the response marks it as a duplicate."""
        body = json.dumps({
            "urls": ["https://t.me/channel/123?fbclid=xyz"],
            "project_id": str(self.project.pk),
        })
        resp = self.client.post(
            self.url, body, content_type="application/json", **self.auth()
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("https://t.me/channel/123?fbclid=xyz", data["results"])
        result = data["results"]["https://t.me/channel/123?fbclid=xyz"]
        self.assertTrue(result["duplicate"])
        self.assertIsNotNone(result["record_id"])

    def test_non_duplicate_returns_false(self):
        """GIVEN an unrelated URL
        WHEN /check is called
        THEN duplicate is false and record_id is null."""
        body = json.dumps({
            "urls": ["https://vk.com/wall1_2"],
            "project_id": str(self.project.pk),
        })
        resp = self.client.post(
            self.url, body, content_type="application/json", **self.auth()
        )
        self.assertEqual(resp.status_code, 200)
        result = resp.json()["results"]["https://vk.com/wall1_2"]
        self.assertFalse(result["duplicate"])
        self.assertIsNone(result["record_id"])

    def test_unauthenticated_returns_401(self):
        """GIVEN no Authorization header
        WHEN /check is called
        THEN 401 is returned."""
        body = json.dumps({"urls": [], "project_id": str(self.project.pk)})
        resp = self.client.post(self.url, body, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

    def test_non_member_returns_403(self):
        """GIVEN a token belonging to a non-member of the project
        WHEN /check is called for that project
        THEN 403 is returned."""
        body = json.dumps({"urls": ["https://x"], "project_id": str(self.project.pk)})
        resp = self.client.post(
            self.url, body, content_type="application/json", **self.auth(self.outsider_token)
        )
        self.assertEqual(resp.status_code, 403)

    def test_invalid_json_returns_400(self):
        """GIVEN malformed JSON body
        WHEN /check is called
        THEN 400 is returned."""
        resp = self.client.post(
            self.url, "not json", content_type="application/json", **self.auth()
        )
        self.assertEqual(resp.status_code, 400)
