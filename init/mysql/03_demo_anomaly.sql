-- ============================================================
-- 演示补充数据：制造一家「环比下滑」的门店
-- 店 3（天河城店）上一周期（7~13 天前）GMV 1600，本周期仅 358
-- 环比 -78%，销售看板「异常门店」会出现该店，可点开下钻
-- ============================================================
USE liveops;

INSERT INTO sales_order
(order_id, session_id, store_id, user_id, coupon_id, total_amount, pay_amount, discount_amount, status, channel, create_time, pay_time)
VALUES
('SO20261028000101', 4, 3, 7,  NULL, 288.00, 288.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 12 DAY), DATE_SUB(NOW(), INTERVAL 12 DAY)),
('SO20261028000102', 4, 3, 8,  NULL, 398.00, 398.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 11 DAY), DATE_SUB(NOW(), INTERVAL 11 DAY)),
('SO20261028000103', 4, 3, 9,  NULL, 268.00, 268.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 10 DAY), DATE_SUB(NOW(), INTERVAL 10 DAY)),
('SO20261028000104', 4, 3, 10, NULL, 358.00, 358.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 9 DAY),  DATE_SUB(NOW(), INTERVAL 9 DAY)),
('SO20261028000105', 4, 3, 11, NULL, 288.00, 288.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 8 DAY),  DATE_SUB(NOW(), INTERVAL 8 DAY));

INSERT INTO sales_order_detail
(order_id, sku_id, product_name, spec, price, qty, subtotal, coupon_applied)
VALUES
('SO20261028000101', 26, '电压力锅',       '5L 曜石黑', 288.00, 1, 288.00, 0),
('SO20261028000102', 23, '纳米空气炸锅 Pro', '5L 银色', 398.00, 1, 398.00, 0),
('SO20261028000103', 28, '智能电饭煲',     '4L 厚釜',   268.00, 1, 268.00, 0),
('SO20261028000104', 34, '收纳箱 6件套',   '中号',      358.00, 1, 358.00, 0),
('SO20261028000105', 26, '电压力锅',       '5L 曜石黑', 288.00, 1, 288.00, 0);
