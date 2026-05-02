"""Unit tests for `apps.incidents.utils.normalize_url`."""
from django.test import SimpleTestCase

from apps.incidents.utils import normalize_url


class NormalizeUrlTests(SimpleTestCase):
    def test_strips_utm_params(self):
        """GIVEN a URL with utm_* tracking params
        WHEN normalized
        THEN the utm_* params are stripped while other params survive."""
        result = normalize_url("https://t.me/channel/123?utm_source=x&utm_medium=email&q=parrot")
        self.assertEqual(result, "https://t.me/channel/123?q=parrot")

    def test_strips_fbclid(self):
        """GIVEN a URL with fbclid
        WHEN normalized
        THEN fbclid is removed."""
        result = normalize_url("https://example.com/post?fbclid=AbC123")
        self.assertEqual(result, "https://example.com/post")

    def test_strips_multiple_known_trackers(self):
        """GIVEN a URL with multiple tracker params (gclid, ref, _ga)
        WHEN normalized
        THEN all are stripped."""
        result = normalize_url(
            "https://x.com/u/1?gclid=A&ref=newsletter&_ga=GA1.2&keep=yes"
        )
        self.assertEqual(result, "https://x.com/u/1?keep=yes")

    def test_lowercases_host(self):
        """GIVEN a URL with mixed-case host
        WHEN normalized
        THEN the host is lowercased while the path keeps its case."""
        result = normalize_url("https://VK.COM/Wall12345_678")
        self.assertEqual(result, "https://vk.com/Wall12345_678")

    def test_strips_trailing_slash(self):
        """GIVEN a URL with a trailing slash on a non-root path
        WHEN normalized
        THEN the trailing slash is removed."""
        result = normalize_url("https://vk.com/wall12345_678/")
        self.assertEqual(result, "https://vk.com/wall12345_678")

    def test_preserves_root_slash(self):
        """GIVEN a URL whose path is exactly '/'
        WHEN normalized
        THEN the root slash is preserved."""
        result = normalize_url("https://example.com/")
        self.assertEqual(result, "https://example.com/")

    def test_empty_input_returns_empty(self):
        """GIVEN empty input
        WHEN normalized
        THEN empty string is returned."""
        self.assertEqual(normalize_url(""), "")
        self.assertEqual(normalize_url("   "), "")

    def test_unparseable_returns_empty(self):
        """GIVEN input without a netloc
        WHEN normalized
        THEN empty string is returned."""
        self.assertEqual(normalize_url("not-a-url"), "")

    def test_idempotent(self):
        """GIVEN already-normalized URL
        WHEN normalized again
        THEN result equals input."""
        once = normalize_url("https://t.me/channel/123?utm_source=x&q=parrot")
        twice = normalize_url(once)
        self.assertEqual(once, twice)

    def test_two_variants_normalize_to_same(self):
        """GIVEN two URL variants of the same canonical resource
        WHEN both normalized
        THEN they collapse to identical strings."""
        a = normalize_url("https://t.me/channel/123?utm_source=newsletter")
        b = normalize_url("https://t.me/channel/123?fbclid=abc")
        c = normalize_url("https://T.ME/channel/123/")
        self.assertEqual(a, b)
        self.assertEqual(b, c)
