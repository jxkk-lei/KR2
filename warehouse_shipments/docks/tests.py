from shipments.testing import DatabaseTestCase


class DockTests(DatabaseTestCase):
    def test_docks_include_capacity_kind_and_joined_totals(self):
        response = self.client.get("/docks/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["docks"]), 4)
        first = response.context["docks"][0]
        self.assertEqual((first["name"], first["capacity"], first["dock_kind"]), ("Док 1", 6, "отгрузка"))
        self.assertEqual(first["shipment_count"], 3)
        self.assertEqual(first["loading_count"], 1)
        self.assertContains(response, "Док 7")
        self.assertContains(response, "Кросс-докинг")
        self.assertTemplateUsed(response, "base.html")

    def test_dock_edit_is_visible_in_list_and_detail_on_refresh(self):
        self.execute("UPDATE docks SET name = ?, capacity = ? WHERE id = ?", ("Док Северный", 15, 1))
        self.assertContains(self.client.get("/docks/"), "Док Северный")
        detail = self.client.get("/shipments/laptops-batch/")
        self.assertContains(detail, "Док Северный")
        self.assertEqual(detail.context["shipment"]["dock_capacity"], 15)
        self.assertContains(self.client.get("/shipments/"), "Док Северный")

    def test_left_join_keeps_docks_without_shipments(self):
        self.execute("DELETE FROM shipments WHERE dock_id = ?", (1,))
        response = self.client.get("/docks/")
        dock = response.context["docks"][0]
        self.assertEqual(dock["name"], "Док 1")
        self.assertEqual(dock["shipment_count"], 0)
        self.assertEqual(dock["total_pallets"], 0)

    def test_empty_dock_list(self):
        self.execute("DELETE FROM shipments")
        self.execute("DELETE FROM docks")
        self.assertContains(self.client.get("/docks/"), "Доки ещё не добавлены")
