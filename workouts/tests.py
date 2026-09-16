from django.test import RequestFactory, TestCase
from django.views.generic import TemplateView


class IndexPageTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_index_page_renders_with_autumn_theme(self):
        """Verify the index page renders with 200 status code and autumn theme content."""
        request = self.factory.get("/")
        view = TemplateView.as_view(template_name="index.html")
        response = view(request)
        response.render()

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        # Check philosophical motto and autumn theme elements
        self.assertIn("If you are strong, you have to be", content)
        self.assertIn("theme.css", content)
        self.assertIn("grow_season", content)
        self.assertIn("Autumn Palette: Oak, Maple &amp; Pumpkin", content)
