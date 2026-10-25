-- Именованные SQL-запросы загружаются и выполняются в shipments/db.py.
-- :параметры передаются отдельно в connection.execute(sql, parameters).

-- name: list_shipments
SELECT s.*, d.name AS dock_name, d.capacity AS dock_capacity, d.dock_kind
FROM shipments AS s
JOIN docks AS d ON d.id = s.dock_id
WHERE (:pallets IS NULL OR s.pallets >= :pallets)
  AND (:status = '' OR s.status = :status)
  AND (:goods_kind = '' OR s.goods_kind = :goods_kind)
  AND (:query = '' OR s.title LIKE :search ESCAPE '\')
ORDER BY {order_by}
LIMIT :limit;

-- name: count_filtered
SELECT COUNT(*) AS total
FROM shipments AS s
WHERE (:pallets IS NULL OR s.pallets >= :pallets)
  AND (:status = '' OR s.status = :status)
  AND (:goods_kind = '' OR s.goods_kind = :goods_kind)
  AND (:query = '' OR s.title LIKE :search ESCAPE '\');

-- name: shipment_by_slug
SELECT s.*, d.name AS dock_name, d.capacity AS dock_capacity, d.dock_kind
FROM shipments AS s
JOIN docks AS d ON d.id = s.dock_id
WHERE s.slug = :slug;

-- name: list_docks
SELECT d.id, d.name, d.capacity, d.dock_kind,
       COUNT(s.id) AS shipment_count,
       COALESCE(SUM(CASE WHEN s.status = 'погружается' THEN 1 ELSE 0 END), 0) AS loading_count,
       COALESCE(SUM(s.pallets), 0) AS total_pallets
FROM docks AS d
LEFT JOIN shipments AS s ON s.dock_id = d.id
GROUP BY d.id, d.name, d.capacity, d.dock_kind
ORDER BY d.id;

-- name: overview
SELECT COUNT(*) AS total,
       COALESCE(SUM(pallets), 0) AS pallets,
       COALESCE(SUM(CASE WHEN status = 'запланирована' THEN 1 ELSE 0 END), 0) AS planned,
       COALESCE(SUM(CASE WHEN status = 'погружается' THEN 1 ELSE 0 END), 0) AS loading,
       COALESCE(SUM(CASE WHEN status = 'отгружена' THEN 1 ELSE 0 END), 0) AS shipped,
       COALESCE(ROUND(AVG(duration), 1), 0) AS avg_duration
FROM shipments;

-- name: dock_overview
SELECT COUNT(*) AS total, COALESCE(SUM(capacity), 0) AS capacity FROM docks;

-- name: goods_statistics
SELECT goods_kind, COUNT(*) AS shipment_count, SUM(pallets) AS total_pallets,
       ROUND(AVG(duration), 1) AS avg_duration
FROM shipments
GROUP BY goods_kind
HAVING COUNT(*) >= :min_count
ORDER BY shipment_count DESC, goods_kind ASC;

-- name: status_statistics
SELECT status, COUNT(*) AS shipment_count, SUM(pallets) AS total_pallets
FROM shipments
GROUP BY status
ORDER BY CASE status WHEN 'запланирована' THEN 1 WHEN 'погружается' THEN 2 ELSE 3 END;
