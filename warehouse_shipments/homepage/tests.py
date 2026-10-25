from django.urls import reverse
from shipments.testing import DatabaseTestCase


class HomeTests(DatabaseTestCase):
    def test_home_shows_actual_count_and_named_navigation(self):
        response = self.client.get(reverse("homepage:home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["overview"]["total"], 12)
        self.assertContains(response, "Всего отгрузок")
        self.assertContains(response, ">12</strong>")
        self.assertContains(response, 'href="/docks/"')
        self.assertContains(response, 'href="/shipments/"')
        self.assertContains(response, 'href="/shipments/statistics/"')
        self.assertTemplateUsed(response, "base.html")

    def test_count_changes_after_database_insert(self):
        self.add_shipment()
        response = self.client.get("/")
        self.assertEqual(response.context["overview"]["total"], 13)
        self.assertContains(response, ">13</strong>")

    def test_empty_warehouse_keeps_pages_working(self):
        self.execute("DELETE FROM shipments")
        self.execute("DELETE FROM docks")
        for url in ("/", "/shipments/", "/docks/", "/shipments/statistics/"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.get("/")
        self.assertEqual(response.context["overview"]["total"], 0)
        self.assertContains(response, "Активных погрузок пока нет")

    def test_static_assets_are_referenced(self):
        response = self.client.get("/")
        for asset in ("/static/img/logo.png", "/static/css/style.css", "/static/js/main.js"):
            self.assertContains(response, asset)

    def test_unknown_route_is_friendly_404(self):
        response = self.client.get("/not-a-page/")
        self.assertContains(response, "Здесь пока пусто", status_code=404)
        self.assertNotContains(response, "Traceback", status_code=404)
