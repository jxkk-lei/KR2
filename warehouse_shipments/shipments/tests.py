import io
import sqlite3
from unittest.mock import patch

from django.core.management import call_command
from django.test import override_settings
from django.urls import resolve, reverse

from . import db
from .testing import DatabaseTestCase


class ShipmentListTests(DatabaseTestCase):
    def test_list_is_rendered_from_joined_records_and_card_include(self):
        response = self.client.get("/shipments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["shipments"]), 12)
        self.assertContains(response, "Партия ноутбуков")
        self.assertContains(response, "Док 7")
        self.assertContains(response, "24.10.2026")
        self.assertContains(response, "ЭЛЕКТРОНИКА")
        self.assertTemplateUsed(response, "shipments/includes/shipment_card.html")
        self.assertTemplateUsed(response, "base.html")
        for label in ("Ожидает погрузки", "Погрузка идёт", "Отправлена"):
            self.assertContains(response, label)

    def test_two_pallet_thresholds_return_different_sql_results(self):
        for threshold, expected_count in ((30, 5), (45, 2)):
            with self.subTest(threshold=threshold):
                response = self.client.get("/shipments/", {"pallets": threshold})
                actual_ids = {row["id"] for row in response.context["shipments"]}
                sql_ids = {row[0] for row in self.execute("SELECT id FROM shipments WHERE pallets >= ?", (threshold,))}
                self.assertEqual(actual_ids, sql_ids)
                self.assertEqual(len(actual_ids), expected_count)
                self.assertEqual(response.context["form"]["pallets"].value(), str(threshold))

    def test_zero_pallet_threshold_keeps_all_records(self):
        response = self.client.get("/shipments/", {"pallets": "0"})
        self.assertEqual(len(response.context["shipments"]), 12)

    def test_invalid_filter_values_are_explained_without_crashing(self):
        cases = [
            {"pallets": "abc"}, {"pallets": "-1"}, {"pallets": "1.5"},
            {"pallets": "999999999999999999999999999999"},
            {"pallets": "0 OR 1=1"}, {"limit": "0"}, {"limit": "-5"},
            {"limit": "501"}, {"sort": "pallets; DROP TABLE shipments;"},
            {"status": "unexpected"}, {"q": "x" * 101},
        ]
        for parameters in cases:
            with self.subTest(parameters=parameters):
                response = self.client.get("/shipments/", parameters)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertContains(response, "Проверьте параметры фильтра")
        self.assertEqual(db.get_overview()["total"], 12)

    def test_empty_filter_result_has_clear_message(self):
        response = self.client.get("/shipments/", {"pallets": "1000"})
        self.assertEqual(response.context["shipments"], [])
        self.assertContains(response, "Отгрузки не найдены")

    def test_sorting_and_limit_are_applied_in_sql(self):
        response = self.client.get("/shipments/", {"sort": "pallets_desc", "limit": "2"})
        self.assertEqual([s["pallets"] for s in response.context["shipments"]], [60, 45])
        self.assertEqual(response.context["matched_count"], 12)
        response = self.client.get("/shipments/", {"sort": "pallets_asc", "limit": "2"})
        self.assertEqual([s["pallets"] for s in response.context["shipments"]], [10, 12])

    def test_date_sort_directions(self):
        ascending = self.client.get("/shipments/", {"sort": "date_asc"}).context["shipments"]
        descending = self.client.get("/shipments/", {"sort": "date_desc"}).context["shipments"]
        self.assertEqual([s["id"] for s in ascending], list(reversed([s["id"] for s in descending])))
        self.assertEqual(ascending[0]["slug"], "server-components")
        self.assertEqual(descending[0]["slug"], "meeting-tables")

    def test_combined_filters_and_matched_count_before_limit(self):
        response = self.client.get("/shipments/", {
            "pallets": "30", "status": "погружается", "goods_kind": "электроника",
            "sort": "pallets_desc", "limit": "1",
        })
        self.assertEqual(response.context["matched_count"], 2)
        self.assertEqual([s["slug"] for s in response.context["shipments"]], ["smartphones-batch"])

    def test_search_and_sql_injection_strings_are_parameters(self):
        response = self.client.get("/shipments/", {"q": "ноутбуков"})
        self.assertEqual([s["slug"] for s in response.context["shipments"]], ["laptops-batch"])
        for query in ("' OR 1=1 --", "%", "_"):
            with self.subTest(query=query):
                response = self.client.get("/shipments/", {"q": query})
                self.assertEqual(response.context["shipments"], [])
        self.assertEqual(db.get_overview()["total"], 12)

    def test_database_edit_is_shown_on_next_request(self):
        self.execute("UPDATE shipments SET title = ?, pallets = ? WHERE slug = ?", ("Изменённая партия", 99, "laptops-batch"))
        response = self.client.get("/shipments/", {"pallets": "99"})
        self.assertEqual(len(response.context["shipments"]), 1)
        self.assertContains(response, "Изменённая партия")


class ShipmentDetailTests(DatabaseTestCase):
    def test_slug_detail_contains_all_shipment_and_dock_data(self):
        url = reverse("shipments:detail", kwargs={"slug": "laptops-batch"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for text in ("Партия ноутбуков", "ЭЛЕКТРОНИКА", "24.10.2026", "09:00", "60", "30", "Погрузка идёт", "Док 1", "Отгрузка"):
            self.assertContains(response, text)
        self.assertEqual(response.context["shipment"]["dock_capacity"], 6)
        self.assertContains(response, 'href="/shipments/"')
        self.assertTemplateUsed(response, "base.html")

    def test_detail_link_uses_named_route(self):
        response = self.client.get("/shipments/")
        self.assertContains(response, f'href="{reverse("shipments:detail", args=["laptops-batch"])}"')

    def test_missing_slug_and_invalid_converter_are_404(self):
        for path in ("/shipments/does-not-exist/", "/shipments/invalid.slug/"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, "Здесь пока пусто", status_code=404)
                self.assertNotContains(response, "Traceback", status_code=404)

    def test_statistics_route_is_before_slug_route(self):
        self.assertEqual(resolve("/shipments/statistics/").view_name, "shipments:statistics")
        self.assertEqual(self.client.get("/shipments/statistics/").status_code, 200)


class StatisticsTests(DatabaseTestCase):
    def test_count_group_by_and_having_are_rendered(self):
        response = self.client.get("/shipments/statistics/")
        groups = {g["goods_kind"]: g["shipment_count"] for g in response.context["groups"]}
        self.assertEqual(groups, {"электроника": 5, "мебель": 4})
        self.assertEqual(response.context["overview"]["pallets"], 335)
        self.assertContains(response, "Электроника")
        self.assertContains(response, "Мебель")
        self.assertTemplateUsed(response, "base.html")

    def test_having_threshold_changes_results_and_handles_empty(self):
        response = self.client.get("/shipments/statistics/", {"min_count": "3"})
        self.assertEqual(len(response.context["groups"]), 3)
        response = self.client.get("/shipments/statistics/", {"min_count": "6"})
        self.assertEqual(response.context["groups"], [])
        self.assertContains(response, "Нет типов груза с 6 или более отгрузками")

    def test_having_group_appears_after_new_shipments(self):
        before = self.client.get("/shipments/statistics/").context["groups"]
        self.assertNotIn("одежда", [g["goods_kind"] for g in before])
        self.add_shipment(slug="clothes-extra-1")
        self.add_shipment(slug="clothes-extra-2")
        response = self.client.get("/shipments/statistics/")
        groups = {g["goods_kind"]: g["shipment_count"] for g in response.context["groups"]}
        self.assertEqual(groups["одежда"], 5)
        self.assertEqual(response.context["overview"]["total"], 14)
        self.assertContains(response, "Одежда")

    def test_invalid_statistics_input_is_explained(self):
        for value in ("-1", "abc", "0", "99999999999999999999"):
            with self.subTest(value=value):
                response = self.client.get("/shipments/statistics/", {"min_count": value})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)


class DatabaseTests(DatabaseTestCase):
    def test_seed_is_repeatable_and_preserves_edits(self):
        self.execute("UPDATE docks SET capacity = 17 WHERE id = 1")
        call_command("initdb", stdout=io.StringIO())
        self.assertEqual(db.get_overview()["total"], 12)
        self.assertEqual(db.get_docks()[0]["capacity"], 17)

    def test_foreign_key_unique_slug_and_domain_constraints(self):
        bad_updates = [
            ("UPDATE shipments SET dock_id = ? WHERE id = 1", (999,)),
            ("UPDATE shipments SET slug = ? WHERE id = 2", ("laptops-batch",)),
            ("UPDATE shipments SET slug = ? WHERE id = 1", ("statistics",)),
            ("UPDATE shipments SET status = ? WHERE id = 1", ("unknown",)),
            ("UPDATE shipments SET pallets = ? WHERE id = 1", (-1,)),
            ("UPDATE shipments SET ship_date = ? WHERE id = 1", ("invalid-date",)),
        ]
        for sql, params in bad_updates:
            with self.subTest(sql=sql):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.execute(sql, params)

    def test_connections_close_after_success_and_sql_failure(self):
        captured = []
        original_connect = sqlite3.connect

        def capture(*args, **kwargs):
            conn = original_connect(*args, **kwargs)
            captured.append(conn)
            return conn

        with patch.object(db.sqlite3, "connect", side_effect=capture):
            db.get_docks()
            with self.assertRaises(sqlite3.OperationalError):
                with db.connection() as conn:
                    conn.execute("SELECT * FROM nonexistent_table")
        self.assertEqual(len(captured), 2)
        for conn in captured:
            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")

    def test_database_errors_are_safe_503_on_every_data_page(self):
        for url in ("/", "/docks/", "/shipments/", "/shipments/statistics/", "/shipments/laptops-batch/"):
            with self.subTest(url=url), self.assertLogs("shipments.db", level="ERROR"):
                with patch.object(db.sqlite3, "connect", side_effect=sqlite3.OperationalError("secret internal /path/to/database")):
                    response = self.client.get(url)
                self.assertContains(response, "Не удалось получить данные склада", status_code=503)
                self.assertNotContains(response, "secret internal", status_code=503)
                self.assertNotContains(response, "Traceback", status_code=503)
                self.assertEqual(response["Retry-After"], "30")

    def test_missing_database_does_not_create_empty_file(self):
        missing = self.db_path.parent / "missing.db"
        with override_settings(SHIPMENTS_DB_PATH=missing), self.assertLogs("shipments.db", level="ERROR"):
            response = self.client.get("/shipments/")
        self.assertEqual(response.status_code, 503)
        self.assertFalse(missing.exists())

    def test_every_named_sql_query_has_a_working_web_scenario(self):
        self.assertEqual(set(db.load_queries()), {
            "list_shipments", "count_filtered", "shipment_by_slug", "list_docks",
            "overview", "dock_overview", "goods_statistics", "status_statistics",
        })
        with patch.object(db, "fetch_all", wraps=db.fetch_all) as fetch:
            for url in ("/", "/docks/", "/shipments/", "/shipments/statistics/", "/shipments/laptops-batch/"):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual({call.args[0] for call in fetch.call_args_list}, set(db.load_queries()))
