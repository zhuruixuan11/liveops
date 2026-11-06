SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ============================
-- 门店 12 家
-- ============================
INSERT INTO store (store_id, name, city, address, manager, status) VALUES
(1,  '星耀广场店',   '上海', '上海市浦东新区世纪大道88号',       '张伟',   1),
(2,  '中心城店',     '北京', '北京市朝阳区建国路88号',           '李娜',   1),
(3,  '天河城店',     '广州', '广州市天河区天河路208号',         '王强',   1),
(4,  '万象城店',     '深圳', '深圳市罗湖区宝安南路1881号',       '刘芳',   1),
(5,  '银泰城店',     '杭州', '杭州市西湖区延安路98号',           '陈明',   1),
(6,  '太古里店',     '成都', '成都市锦江区中纱帽街8号',         '杨丽',   1),
(7,  '武商广场店',   '武汉', '武汉市江汉区解放大道688号',       '赵刚',   1),
(8,  '德基广场店',   '南京', '南京市玄武区中山路18号',           '黄敏',   1),
(9,  '赛格店',       '西安', '西安市雁塔区长安中路65号',         '周杰',   1),
(10, '解放碑店',     '重庆', '重庆市渝中区解放碑步行街',         '吴婷',   1),
(11, '劝业场店',     '天津', '天津市和平区和平路290号',         '郑浩',   1),
(12, '观前街店',     '苏州', '苏州市姑苏区观前街100号',         '孙丽',   1);

-- ============================
-- auth_user
-- ============================
INSERT INTO auth_user (user_id, username, password_hash, phone, role, status) VALUES
(1,  'admin1',    '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000001', 'ADMIN',    1),
(2,  'op1',       '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000002', 'OPERATOR', 1),
(3,  'op2',       '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000003', 'OPERATOR', 1),
(4,  'host1',     '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000004', 'HOST',     1),
(5,  'host2',     '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000005', 'HOST',     1),
(6,  'host3',     '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000006', 'HOST',     1),
(7,  'customer1', '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000011', 'CUSTOMER', 1),
(8,  'customer2', '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000012', 'CUSTOMER', 1),
(9,  'customer3', '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000013', 'CUSTOMER', 1),
(10, 'customer4', '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000014', 'CUSTOMER', 1),
(11, 'customer5', '$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.', '13800000015', 'CUSTOMER', 1);

-- ============================
-- staff: 12 store x 3 = 36
-- 规划：
--   store 1: host_id=1(USER4) / manager=12(USER12) / op=23(USER23)
--   store 2: host_id=2(USER5) / manager=13(USER13) / op=24(USER24)
--   ... 以此类推
-- user_id: manager 从 12~23，host 从 4~6 复用，op 从 24~35
-- 为简洁起见，先补齐 auth_user 中缺失的 staff user
-- ============================
INSERT INTO auth_user (username, password_hash, phone, role) VALUES
('mgr1','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000021','OPERATOR'),
('mgr2','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000022','OPERATOR'),
('mgr3','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000023','OPERATOR'),
('mgr4','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000024','OPERATOR'),
('mgr5','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000025','OPERATOR'),
('mgr6','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000026','OPERATOR'),
('mgr7','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000027','OPERATOR'),
('mgr8','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000028','OPERATOR'),
('mgr9','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000029','OPERATOR'),
('mgr10','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000030','OPERATOR'),
('mgr11','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000031','OPERATOR'),
('mgr12','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000032','OPERATOR'),
('op3','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000033','OPERATOR'),
('op4','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000034','OPERATOR'),
('op5','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000035','OPERATOR'),
('op6','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000036','OPERATOR'),
('op7','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000037','OPERATOR'),
('op8','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000038','OPERATOR'),
('op9','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000039','OPERATOR'),
('op10','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000040','OPERATOR'),
('op11','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000041','OPERATOR'),
('op12','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000042','OPERATOR'),
('host4','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000043','HOST'),
('host5','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000044','HOST'),
('host6','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000045','HOST'),
('host7','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000046','HOST'),
('host8','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000047','HOST'),
('host9','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000048','HOST'),
('host10','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000049','HOST'),
('host11','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000050','HOST'),
('host12','$2b$12$z.NytxqR1lKeBqH1jSsPzuj48MzLhLWLy1bbQV4dMU4FA.AFCSUg.','13800000051','HOST');

-- staff user_id 规划：
--   manager: user_id 12~23 (mgr1~mgr12)
--   host:    user_id 4~6  +  36~45 (host1..host12)   -> 用 36..47 这样清晰
--   op:      user_id 2~3  +  24~35 (op1..op12)       -> 用 24..35 清晰
-- 让我重新统一：host 用 36~47，manager 用 12~23，op 用 24~35
INSERT INTO staff (staff_id, store_id, user_id, name, role, availability, status, max_concurrent) VALUES
-- store 1 上海: manager=12, host=36, op=24
(1,  1, 36, '林小美', 'HOST',     '工作日18:00-22:00 周末全天', 'online', 5),
(2,  1, 12, '张伟',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(3,  1, 24, '陈晨',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 2 北京
(4,  2, 37, '王甜甜', 'HOST',     '工作日19:00-23:00 周末全天', 'online', 5),
(5,  2, 13, '李娜',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(6,  2, 25, '刘强',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 3 广州
(7,  3, 38, '阿Ling', 'HOST',     '工作日18:30-22:30',         'online', 5),
(8,  3, 14, '王强',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(9,  3, 26, '何志',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 4 深圳
(10, 4, 39, '周雨桐', 'HOST',     '工作日19:00-23:00',         'online', 5),
(11, 4, 15, '刘芳',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(12, 4, 27, '吴浩',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 5 杭州
(13, 5, 40, '苏西子', 'HOST',     '工作日18:00-22:00',         'online', 5),
(14, 5, 16, '陈明',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(15, 5, 28, '郑颖',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 6 成都
(16, 6, 41, '川妹子', 'HOST',     '工作日19:00-23:00',         'online', 5),
(17, 6, 17, '杨丽',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(18, 6, 29, '韩磊',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 7 武汉
(19, 7, 42, '热干面', 'HOST',     '工作日18:00-22:00',         'online', 5),
(20, 7, 18, '赵刚',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(21, 7, 30, '曹磊',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 8 南京
(22, 8, 43, '美龄宫', 'HOST',     '工作日19:00-23:00',         'online', 5),
(23, 8, 19, '黄敏',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(24, 8, 31, '石磊',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 9 西安
(25, 9, 44, '古都妹', 'HOST',     '工作日18:00-22:00',         'online', 5),
(26, 9, 20, '周杰',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(27, 9, 32, '马超',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 10 重庆
(28, 10, 45, '辣妹子', 'HOST',     '工作日19:00-23:00',         'online', 5),
(29, 10, 21, '吴婷',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(30, 10, 33, '江伟',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 11 天津
(31, 11, 46, '天津姐', 'HOST',     '工作日18:00-22:00',         'online', 5),
(32, 11, 22, '郑浩',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(33, 11, 34, '刘洋',   'OPERATOR', '工作日10:00-22:00',         'online', 5),
-- store 12 苏州
(34, 12, 47, '江南秀', 'HOST',     '工作日19:00-23:00',         'online', 5),
(35, 12, 23, '孙丽',   'MANAGER',  '工作日9:00-18:00',          'online', 5),
(36, 12, 35, '徐阳',   'OPERATOR', '工作日10:00-22:00',         'online', 5);

-- ============================
-- product_category 3 级
-- 一级 4 个：美容护肤 / 家居生活 / 数码潮品 / 食品饮料
-- ============================
INSERT INTO product_category (category_id, parent_id, name, level, sort_order, is_show) VALUES
-- 一级
(1,  NULL, '美容护肤', 1, 1, 1),
(2,  NULL, '家居生活', 1, 2, 1),
(3,  NULL, '数码潮品', 1, 3, 1),
(4,  NULL, '食品饮料', 1, 4, 1),
-- 二级 - 美容护肤
(101, 1, '面部护肤',   2, 1, 1),
(102, 1, '彩妆唇妆',   2, 2, 1),
(103, 1, '身体护理',   2, 3, 1),
-- 二级 - 家居生活
(201, 2, '厨房电器',   2, 1, 1),
(202, 2, '清洁收纳',   2, 2, 1),
-- 二级 - 数码潮品
(301, 3, '音频设备',   2, 1, 1),
(302, 3, '智能穿戴',   2, 2, 1),
(303, 3, '手机配件',   2, 3, 1),
-- 二级 - 食品饮料
(401, 4, '咖啡茶饮',   2, 1, 1),
(402, 4, '休闲零食',   2, 2, 1),
(403, 4, '粮油调味',   2, 3, 1);

-- ============================
-- product：50+ 商品
-- ============================
INSERT INTO product (product_id, category_id, product_name, subtitle, brand, main_image, description, status, sales_count) VALUES
-- ========== 101 面部护肤 ==========
(1,  101, '玻尿酸保湿精华液',     '深层补水 清爽不黏腻 30ml',   '水润堂',   'https://img.liveops.io/p/001.jpg', '富含大、小、微三种分子量玻尿酸，24小时长效保湿。适合油皮、混油皮。', 1, 1280),
(2,  101, '烟酰胺美白祛斑精华',   '5%烟酰胺 温和去黄 30ml',     '水润堂',   'https://img.liveops.io/p/002.jpg', '5%高纯度烟酰胺，搭配神经酰胺修护屏障，提亮肤色淡化色斑。', 1, 980),
(3,  101, '视黄醇抗老眼霜',       '0.5%视黄醇 淡纹提亮眼周 20g','逆时光',   'https://img.liveops.io/p/003.jpg', '0.5%缓释视黄醇+咖啡因，对抗细纹、黑眼圈、浮肿三重眼周问题。', 1, 756),
(4,  101, '氨基酸洁面乳',         '温和清洁 不紧绷 120g',       '清润',     'https://img.liveops.io/p/004.jpg', '纯氨基酸表活，PH值接近肌肤，敏感肌可用。', 1, 2100),
(5,  101, '神经酰胺修护面霜',     '强韧屏障 50g',              '水润堂',   'https://img.liveops.io/p/005.jpg', '三重神经酰胺+胆固醇+脂肪酸，仿生修护受损屏障。', 1, 620),
-- ========== 102 彩妆唇妆 ==========
(6,  102, '丝绒哑光口红 #正红',   '显白不挑皮 持久不脱妆 3.5g','俏唇',     'https://img.liveops.io/p/006.jpg', '丝绒哑光质地，显色浓郁不拔干，喝水不沾杯。', 1, 3400),
(7,  102, '水光唇釉 #豆沙粉',     '镜面水光 少女感 6g',         '俏唇',     'https://img.liveops.io/p/007.jpg', '成膜快，玻璃唇妆效，保湿透亮。', 1, 2100),
(8,  102, '持妆粉底液 #自然色',   '遮瑕持妆 不卡粉 30ml',       '悦颜',     'https://img.liveops.io/p/008.jpg', '24小时持妆，遮瑕力中等，适合干皮。', 1, 1890),
(9,  102, '散粉定妆粉 透明色',   '控油持妆 不假面 10g',         '悦颜',     'https://img.liveops.io/p/009.jpg', '微米级粉质，上脸雾面柔焦。', 1, 1560),
-- ========== 103 身体护理 ==========
(10, 103, '香氛沐浴露 樱花款',   '持久留香 温和洁净 500ml',     '香氛集',   'https://img.liveops.io/p/010.jpg', '前调樱花 中调玫瑰 后调麝香，泡沫绵密。', 1, 870),
(11, 103, '烟酰胺身体乳',         '美白保湿 300ml',             '水润堂',   'https://img.liveops.io/p/011.jpg', '3%烟酰胺+乳木果油，身体白白嫩嫩。', 1, 650),
(12, 103, '去角质磨砂膏',         '温和去角质 250g',            '清润',     'https://img.liveops.io/p/012.jpg', '胡桃壳颗粒+乳酸，温和去除老废角质。', 1, 320),

-- ========== 201 厨房电器 ==========
(13, 201, '纳米空气炸锅 Pro',     '5L大容量 无油健康',          '厨乐',     'https://img.liveops.io/p/013.jpg', '纳米不沾内胆，360°热风循环，一键脆皮。', 1, 1250),
(14, 201, '破壁料理机',           '多功能家用 1.75L',           '厨乐',     'https://img.liveops.io/p/014.jpg', '40000转高速破壁，豆浆/辅食/冰沙一键搞定。', 1, 980),
(15, 201, '电压力锅 智能款',       '5L双胆 24H预约',             '厨乐',     'https://img.liveops.io/p/015.jpg', 'IH电磁加热，双胆不串味，老人也能轻松操作。', 1, 760),
(16, 201, '智能电饭煲',           'IH电磁加热 4L',              '米粒',     'https://img.liveops.io/p/016.jpg', '日本IH技术，厚釜内胆，煮出粒粒分明好米饭。', 1, 1100),
(17, 201, '胶囊咖啡机',           '一键萃取 多口味',            '豆叔',     'https://img.liveops.io/p/017.jpg', '高压19Bar萃取，兼容多品牌胶囊。', 1, 540),
-- ========== 202 清洁收纳 ==========
(18, 202, '无线吸尘器 V11',       '25000Pa大吸力 60min续航',    '洁净家',   'https://img.liveops.io/p/018.jpg', '数码电机+多锥旋风，可换多种吸头。', 1, 860),
(19, 202, '全自动扫地机器人',     '激光导航 拖扫一体',          '洁净家',   'https://img.liveops.io/p/019.jpg', 'LDS激光建图，自动回充，扫拖一体。', 1, 670),
(20, 202, '收纳箱 6件套',         '加厚PP 可叠放',              '家宜',     'https://img.liveops.io/p/020.jpg', '6个不同尺寸，家庭收纳一套搞定。', 1, 430),

-- ========== 301 音频设备 ==========
(21, 301, '降噪蓝牙耳机 X7',       '主动降噪 40小时续航',        '音浪',     'https://img.liveops.io/p/021.jpg', '行业领先-42dB主动降噪，Hi-Res认证。', 1, 2340),
(22, 301, '真无线耳机 Mini',       '轻巧舒适 入耳检测',          '音浪',     'https://img.liveops.io/p/022.jpg', '单耳仅4g，IPX5防水，智能入耳检测。', 1, 1980),
(23, 301, '便携蓝牙音箱',         '360°环绕 IPX7防水',          '音浪',     'https://img.liveops.io/p/023.jpg', 'IPX7级防水，20小时续航，户外首选。', 1, 560),
(24, 301, '桌面HIFI音箱',          '双分频 大功率',              '原音',     'https://img.liveops.io/p/024.jpg', '高保真双分频，木质箱体，客厅发烧。', 1, 320),
-- ========== 302 智能穿戴 ==========
(25, 302, '智能运动手表 S2',       '血氧心率 GPS 14天续航',      '环宇',     'https://img.liveops.io/p/025.jpg', 'AMOLED屏，支持100+运动模式。', 1, 1870),
(26, 302, '健康监测手环',         '全天候心率血氧 睡眠监测',    '环宇',     'https://img.liveops.io/p/026.jpg', '1.1寸彩屏，10天超长续航。', 1, 1450),
(27, 302, '智能戒指',             '睡眠/运动/压力监测',         '环宇',     'https://img.liveops.io/p/027.jpg', '最轻仅4g，7天续航，防水50米。', 1, 230),
-- ========== 303 手机配件 ==========
(28, 303, '65W氮化镓快充',        '三口同充 折叠插脚',          '闪充',     'https://img.liveops.io/p/028.jpg', 'GaN技术 65W PD快充，三口同时输出。', 1, 3200),
(29, 303, '磁吸无线充电宝 10000mAh','Magsafe磁吸 超薄便携',     '闪充',     'https://img.liveops.io/p/029.jpg', 'Magsafe一吸即充，带支架功能。', 1, 2100),
(30, 303, '碳纤维手机壳 iPhone15', '轻薄防摔 支持MagSafe',       '铠甲',     'https://img.liveops.io/p/030.jpg', '芳纶纤维材质，仅1.2mm薄。', 1, 980),
(31, 303, '高清钢化膜',           '0.3mm 全屏覆盖',             '铠甲',     'https://img.liveops.io/p/031.jpg', '9H硬度，防指纹疏油层。', 1, 4500),

-- ========== 401 咖啡茶饮 ==========
(32, 401, '低温冷萃咖啡胶囊',     '100%阿拉比卡 12粒',          '豆叔',     'https://img.liveops.io/p/032.jpg', '低温冷萃12小时，还原咖啡店风味。', 1, 2560),
(33, 401, '挂耳咖啡礼盒 10种风味', '精品产地 100包',             '豆叔',     'https://img.liveops.io/p/033.jpg', '10种不同产区挂耳，咖啡入门首选。', 1, 1890),
(34, 401, '茉莉花茶 特级',         '香浓耐泡 200g',              '茶颜',     'https://img.liveops.io/p/034.jpg', '福建福州特级茉莉花茶，七窨一提。', 1, 780),
(35, 401, '云南普洱熟茶饼',       '357g 陈香浓郁',              '茶颜',     'https://img.liveops.io/p/035.jpg', '云南勐海普洱熟茶，越陈越香。', 1, 430),
-- ========== 402 休闲零食 ==========
(36, 402, '每日坚果 30袋装',       '6种坚果 科学配比',           '果子熟了', 'https://img.liveops.io/p/036.jpg', '30袋独立小包装，每日一包营养满满。', 1, 3400),
(37, 402, '手工曲奇礼盒',         '黄油香酥 600g',              '甜蜜时光', 'https://img.liveops.io/p/037.jpg', '法式黄油曲奇，松脆入口即化。', 1, 1280),
(38, 402, '高蛋白能量棒',         '健身代餐 20支',              '能量补给', 'https://img.liveops.io/p/038.jpg', '20g蛋白质/支，健身好搭档。', 1, 960),
(39, 402, '无添加水果干礼盒',     '芒果/草莓/蓝莓 500g',        '果子熟了', 'https://img.liveops.io/p/039.jpg', '0添加糖，纯水果烘干。', 1, 670),
-- ========== 403 粮油调味 ==========
(40, 403, '东北五常大米 5kg',     '稻花香2号 新米',             '粮心',     'https://img.liveops.io/p/040.jpg', '黑龙江五常稻花香2号，粒粒饱满。', 1, 890),
(41, 403, '特级初榨橄榄油 1L',   '西班牙进口 冷压榨',           '油管家',   'https://img.liveops.io/p/041.jpg', 'PDO认证，酸度≤0.3%。', 1, 560),
(42, 403, '酿造生抽 500ml',       '老配方酿造 鲜味足',           '酱好吃',   'https://img.liveops.io/p/042.jpg', '180天发酵酿造，自然鲜甜。', 1, 210);

-- ============================
-- sku_info：每个商品 1-4 个 SKU，total 100+
-- 埋入 2 个库存告急：sku_id=15 (product_id=4 氨基酸洁面乳 旅行装), sku_id=30 (product_id=15 电压力锅 白色款)
-- ============================
INSERT INTO sku_info (sku_id, product_id, sku_code, spec, price, original_price, stock, image) VALUES
-- product 1
(1,  1, 'SKU-000001', '30ml',         128.00, 168.00, 300, 'https://img.liveops.io/sku/001.jpg'),
(2,  1, 'SKU-000002', '30ml*2 家庭装',238.00, 336.00, 200, 'https://img.liveops.io/sku/002.jpg'),
-- product 2
(3,  2, 'SKU-000003', '30ml',         198.00, 258.00, 180, 'https://img.liveops.io/sku/003.jpg'),
(4,  2, 'SKU-000004', '30ml*2',       358.00, 516.00, 120, 'https://img.liveops.io/sku/004.jpg'),
-- product 3
(5,  3, 'SKU-000005', '20g',          268.00, 328.00, 150, 'https://img.liveops.io/sku/005.jpg'),
-- product 4 氨基酸洁面乳 —— 埋库存告急！
(6,  4, 'SKU-000006', '120g 正装',     58.00,  78.00, 400, 'https://img.liveops.io/sku/006.jpg'),
(7,  4, 'SKU-000007', '30g 旅行装',    19.90,  29.90,  8,  'https://img.liveops.io/sku/007.jpg'),  -- stock=8 告急
(8,  4, 'SKU-000008', '120g*2',        99.00, 156.00, 250, 'https://img.liveops.io/sku/008.jpg'),
-- product 5
(9,  5, 'SKU-000009', '50g',           258.00, 318.00, 180, 'https://img.liveops.io/sku/009.jpg'),
-- product 6
(10, 6, 'SKU-000010', '#正红 3.5g',      168.00, 228.00, 500, 'https://img.liveops.io/sku/010.jpg'),
(11, 6, 'SKU-000011', '#玫瑰红 3.5g',    168.00, 228.00, 420, 'https://img.liveops.io/sku/011.jpg'),
(12, 6, 'SKU-000012', '#豆沙色 3.5g',    168.00, 228.00, 380, 'https://img.liveops.io/sku/012.jpg'),
-- product 7
(13, 7, 'SKU-000013', '#豆沙粉 6g',      128.00, 168.00, 360, 'https://img.liveops.io/sku/013.jpg'),
(14, 7, 'SKU-000014', '#番茄红 6g',      128.00, 168.00, 280, 'https://img.liveops.io/sku/014.jpg'),
-- product 8
(15, 8, 'SKU-000015', '自然色 30ml',     299.00, 399.00, 150, 'https://img.liveops.io/sku/015.jpg'),
(16, 8, 'SKU-000016', '象牙白 30ml',     299.00, 399.00, 120, 'https://img.liveops.io/sku/016.jpg'),
-- product 9
(17, 9, 'SKU-000017', '透明色 10g',      88.00, 118.00, 450, 'https://img.liveops.io/sku/017.jpg'),
(18, 9, 'SKU-000018', '自然色 10g',      88.00, 118.00, 320, 'https://img.liveops.io/sku/018.jpg'),
-- product 10
(19, 10,'SKU-000019', '樱花 500ml',      78.00,  108.00, 280, 'https://img.liveops.io/sku/019.jpg'),
(20, 10,'SKU-000020', '玫瑰 500ml',      78.00,  108.00, 260, 'https://img.liveops.io/sku/020.jpg'),
-- product 11
(21, 11,'SKU-000021', '300ml',          68.00,  98.00, 220, 'https://img.liveops.io/sku/021.jpg'),
-- product 12
(22, 12,'SKU-000022', '250g',           48.00,  68.00, 180, 'https://img.liveops.io/sku/022.jpg'),
-- product 13
(23, 13,'SKU-000023', '5L 银色',        399.00, 599.00, 120, 'https://img.liveops.io/sku/023.jpg'),
(24, 13,'SKU-000024', '5L 星空蓝',      429.00, 629.00, 100, 'https://img.liveops.io/sku/024.jpg'),
-- product 14
(25, 14,'SKU-000025', '1.75L',          359.00, 499.00, 80, 'https://img.liveops.io/sku/025.jpg'),
-- product 15 电压力锅 —— 埋第二个库存告急
(26, 15,'SKU-000026', '5L 曜石黑',      459.00, 699.00, 95,  'https://img.liveops.io/sku/026.jpg'),
(27, 15,'SKU-000027', '5L 珍珠白',      459.00, 699.00, 12,  'https://img.liveops.io/sku/027.jpg'),  -- stock=12 告急
-- product 16
(28, 16,'SKU-000028', '4L 厚釜',        499.00, 699.00, 130, 'https://img.liveops.io/sku/028.jpg'),
-- product 17
(29, 17,'SKU-000029', '黑色主机 + 20粒胶囊', 399.00, 549.00, 60, 'https://img.liveops.io/sku/029.jpg'),
(30, 17,'SKU-000030', '白色主机 + 20粒胶囊', 399.00, 549.00, 55, 'https://img.liveops.io/sku/030.jpg'),
-- product 18
(31, 18,'SKU-000031', 'V11 标准版',      1899.00, 2499.00, 40, 'https://img.liveops.io/sku/031.jpg'),
(32, 18,'SKU-000032', 'V11 豪华套装',    2299.00, 2999.00, 25, 'https://img.liveops.io/sku/032.jpg'),
-- product 19
(33, 19,'SKU-000033', 'S8 Pro 激光版',   1999.00, 2799.00, 30, 'https://img.liveops.io/sku/033.jpg'),
-- product 20
(34, 20,'SKU-000034', '6件套 中号',      159.00,  219.00, 300, 'https://img.liveops.io/sku/034.jpg'),
-- product 21
(35, 21,'SKU-000035', 'X7 曜石黑',        899.00, 1299.00, 200, 'https://img.liveops.io/sku/035.jpg'),
(36, 21,'SKU-000036', 'X7 云岩白',        899.00, 1299.00, 180, 'https://img.liveops.io/sku/036.jpg'),
-- product 22
(37, 22,'SKU-000037', 'Mini 黑',          299.00,  399.00, 400, 'https://img.liveops.io/sku/037.jpg'),
(38, 22,'SKU-000038', 'Mini 白',          299.00,  399.00, 350, 'https://img.liveops.io/sku/038.jpg'),
(39, 22,'SKU-000039', 'Mini 蓝',          329.00,  429.00, 200, 'https://img.liveops.io/sku/039.jpg'),
-- product 23
(40, 23,'SKU-000040', '经典款 黑',        399.00,  549.00, 150, 'https://img.liveops.io/sku/040.jpg'),
-- product 24
(41, 24,'SKU-000041', '木质书架箱',       599.00,  899.00, 50, 'https://img.liveops.io/sku/041.jpg'),
-- product 25
(42, 25,'SKU-000042', 'S2 黑',            799.00, 1099.00, 180, 'https://img.liveops.io/sku/042.jpg'),
(43, 25,'SKU-000043', 'S2 玫瑰金',        829.00, 1129.00, 120, 'https://img.liveops.io/sku/043.jpg'),
-- product 26
(44, 26,'SKU-000044', 'B6 手环',          199.00,  279.00, 500, 'https://img.liveops.io/sku/044.jpg'),
-- product 27
(45, 27,'SKU-000045', '智能戒指 7号',     389.00,  529.00, 30, 'https://img.liveops.io/sku/045.jpg'),
-- product 28
(46, 28,'SKU-000046', '65W GaN 三口',     128.00,  179.00, 600, 'https://img.liveops.io/sku/046.jpg'),
-- product 29
(47, 29,'SKU-000047', '磁吸充电宝 10000mAh', 199.00, 279.00, 300, 'https://img.liveops.io/sku/047.jpg'),
-- product 30
(48, 30,'SKU-000048', 'iPhone15 芳纶壳', 129.00,  189.00, 200, 'https://img.liveops.io/sku/048.jpg'),
-- product 31
(49, 31,'SKU-000049', 'iPhone15 钢化膜',  29.90,   49.90, 800, 'https://img.liveops.io/sku/049.jpg'),
(50, 31,'SKU-000050', '通用 6.7寸',       39.90,   59.90, 600, 'https://img.liveops.io/sku/050.jpg'),
-- product 32
(51, 32,'SKU-000051', '冷萃咖啡 12粒',     59.00,   89.00, 400, 'https://img.liveops.io/sku/051.jpg'),
(52, 32,'SKU-000052', '冷萃咖啡 36粒',    159.00,  267.00, 280, 'https://img.liveops.io/sku/052.jpg'),
-- product 33
(53, 33,'SKU-000053', '10种风味 100包礼盒', 299.00, 399.00, 200, 'https://img.liveops.io/sku/053.jpg'),
-- product 34
(54, 34,'SKU-000054', '特级茉莉花 200g',   88.00,  128.00, 150, 'https://img.liveops.io/sku/054.jpg'),
-- product 35
(55, 35,'SKU-000055', '普洱熟茶 357g',    158.00,  218.00, 80, 'https://img.liveops.io/sku/055.jpg'),
-- product 36
(56, 36,'SKU-000056', '每日坚果 30袋',     89.00,  128.00, 500, 'https://img.liveops.io/sku/056.jpg'),
-- product 37
(57, 37,'SKU-000057', '曲奇礼盒 600g',    128.00,  178.00, 180, 'https://img.liveops.io/sku/057.jpg'),
-- product 38
(58, 38,'SKU-000058', '能量棒 20支装',     79.00,  119.00, 250, 'https://img.liveops.io/sku/058.jpg'),
-- product 39
(59, 39,'SKU-000059', '水果干礼盒 500g',   99.00,  138.00, 200, 'https://img.liveops.io/sku/059.jpg'),
-- product 40
(60, 40,'SKU-000060', '五常大米 5kg',      69.90,   99.90, 300, 'https://img.liveops.io/sku/060.jpg'),
(61, 40,'SKU-000061', '五常大米 10kg',    129.00,  189.00, 200, 'https://img.liveops.io/sku/061.jpg'),
-- product 41
(62, 41,'SKU-000062', '初榨橄榄油 1L',     98.00,  138.00, 160, 'https://img.liveops.io/sku/062.jpg'),
-- product 42
(63, 42,'SKU-000063', '酿造生抽 500ml',    29.90,   49.90, 450, 'https://img.liveops.io/sku/063.jpg');

-- ============================
-- intent_label 10 条
-- ============================
INSERT INTO intent_label (intent, label_name, route_to, need_hitl) VALUES
('faq_product',  '商品咨询',       'FAQ',    0),
('faq_policy',   '政策咨询',       'FAQ',    0),
('ask_coupon',   '索要优惠券',     'COUPON', 0),
('ask_stock',    '库存查询',       'STOCK',  0),
('ask_price',    '价格咨询',       'FAQ',    0),
('logistics',    '物流咨询',       'HUMAN',  1),
('aftersale',    '售后问题',       'HUMAN',  1),
('complaint',    '投诉建议',       'HUMAN',  1),
('spam',         '垃圾/恶意弹幕',  'FILTER', 0),
('general',      '闲聊/通用',      'FAQ',    0);

-- ============================
-- live_session 15 场
-- session_id=1 living 美妆场  (上海星耀广场 store_id=1, host_id=1 林小美)
-- session_id=2 living 家居场  (低流量)
-- 其余为过去或未来场
-- ============================
INSERT INTO live_session (session_id, store_id, host_id, title, start_time, end_time, status, viewer_count, peak_viewer) VALUES
(1,  1,  1,  '【限时特惠】双11美妆专场',        DATE_SUB(NOW(), INTERVAL 70 MINUTE), NULL,  'living', 528, 863),
(2,  5,  13, '家居焕新季·超值好物',             DATE_SUB(NOW(), INTERVAL 45 MINUTE), NULL,  'living', 12,  45),
(3,  2,  4,  '数码潮品之夜 蓝牙耳机专场',       DATE_SUB(NOW(), INTERVAL 2 DAY),    DATE_SUB(NOW(), INTERVAL 1 DAY), 'ended',  1204, 2310),
(4,  3,  7,  '广州美食节·速食大促',             DATE_SUB(NOW(), INTERVAL 3 DAY),    DATE_SUB(NOW(), INTERVAL 3 DAY), 'ended',  876, 1520),
(5,  4,  10, '智能穿戴·手表手环热卖',           DATE_SUB(NOW(), INTERVAL 1 DAY),    DATE_SUB(NOW(), INTERVAL 20 HOUR),'ended',  543, 987),
(6,  6,  16, '成都好货·零食专场',               DATE_SUB(NOW(), INTERVAL 2 DAY),    DATE_SUB(NOW(), INTERVAL 1 DAY), 'ended',  620, 1100),
(7,  7,  19, '武汉严选·粮油调味',               DATE_SUB(NOW(), INTERVAL 4 DAY),    DATE_SUB(NOW(), INTERVAL 4 DAY), 'ended',  430, 820),
(8,  8,  22, '南京茶颜·精品茶叶专场',           DATE_SUB(NOW(), INTERVAL 5 DAY),    DATE_SUB(NOW(), INTERVAL 5 DAY), 'ended',  210, 405),
(9,  9,  25, '古都好物·护肤大促',               DATE_SUB(NOW(), INTERVAL 6 DAY),    DATE_SUB(NOW(), INTERVAL 6 DAY), 'ended',  780, 1340),
(10, 10, 28, '辣妹子·重庆火锅底料专场',         DATE_SUB(NOW(), INTERVAL 3 DAY),    DATE_SUB(NOW(), INTERVAL 3 DAY), 'ended',  1020, 1890),
(11, 11, 31, '天津港货·进口零食',               DATE_ADD(NOW(), INTERVAL 6 HOUR),   NULL,  'planned', 0,   0),
(12, 12, 34, '江南好物·丝绸围巾',               DATE_ADD(NOW(), INTERVAL 1 DAY),    NULL,  'planned', 0,   0),
(13, 1,  1,  '美妆狂欢·大牌返场',               DATE_ADD(NOW(), INTERVAL 2 DAY),    NULL,  'planned', 0,   0),
(14, 2,  4,  '年末数码狂欢夜',                   DATE_SUB(NOW(), INTERVAL 1 DAY),    DATE_SUB(NOW(), INTERVAL 1 DAY), 'ended',  1580, 2890),
(15, 3,  7,  '广东早茶点心上新',                 DATE_SUB(NOW(), INTERVAL 5 DAY),    DATE_SUB(NOW(), INTERVAL 5 DAY), 'ended',  360, 680);

-- ============================
-- live_product 挂载 —— living 场1 挂 8 个（含 1 个 is_focus=1）
-- living 场2 挂 6 个
-- 注意：living场1 的 focus 选 product_id=4 氨基酸洁面乳 (sku_id=7, stock=8)，对应库存预警
-- ============================
INSERT INTO live_product (session_id, product_id, sku_id, explain_status, order_in_session, is_focus) VALUES
-- session_id=1 美妆场
(1, 1,  1,  'explained', 18, 0),
(1, 2,  3,  'explaining', 5, 0),
(1, 4,  7,  'pending',   0,  1),   -- focus：氨基酸洁面乳 旅行装 stock=8
(1, 6,  10, 'pending',   22, 0),
(1, 8,  15, 'pending',   12, 0),
(1, 5,  9,  'pending',   7,  0),
(1, 10, 19, 'pending',   3,  0),
(1, 11, 21, 'pending',   9,  0),
-- session_id=2 家居场 (低流量)
(2, 13, 23, 'explained', 3,  0),
(2, 14, 25, 'pending',   0,  1),
(2, 16, 28, 'pending',   1,  0),
(2, 18, 31, 'pending',   1,  0),
(2, 19, 33, 'pending',   0,  0),
(2, 20, 34, 'pending',   2,  0);

-- ============================
-- coupon —— 两场 living 各配 2-3 张
-- ============================
INSERT INTO coupon (coupon_id, session_id, type, threshold, discount, stock, issued, valid_start, valid_end) VALUES
-- living 场1
(1, 1, 'percent',  0,    0.15, 500, 128, NOW(), DATE_ADD(NOW(), INTERVAL 2 HOUR)),
(2, 1, 'discount', 199.00, 30.00, 300, 85,  NOW(), DATE_ADD(NOW(), INTERVAL 2 HOUR)),
(3, 1, 'shipping', 0,    0,    999, 420, NOW(), DATE_ADD(NOW(), INTERVAL 3 HOUR)),
-- living 场2
(4, 2, 'percent',  0,    0.10, 200, 18,  NOW(), DATE_ADD(NOW(), INTERVAL 2 HOUR)),
(5, 2, 'discount', 299.00, 50.00, 100, 6,   NOW(), DATE_ADD(NOW(), INTERVAL 2 HOUR)),
-- planned 场11
(6, 11, 'percent',  0,    0.20, 500, 0,   DATE_ADD(NOW(), INTERVAL 6 HOUR), DATE_ADD(NOW(), INTERVAL 8 HOUR));

-- ============================
-- danmaku 100 条左右 —— 分布在 session 1 & 2
-- ============================
INSERT INTO danmaku (session_id, user_id, nickname, content, intent, priority, handled_by, confidence) VALUES
-- ===== living session 1 (美妆场) 约 60 条 =====
(1, 7,  '柠檬不萌',     '主播好漂亮！',                               'general',      3, 'AI',      0.92),
(1, 8,  '咖啡不加糖',   '这个精华适合油皮吗？',                       'faq_product',  2, 'AI',      0.95),
(1, 9,  '爱美的猫',     '有没有优惠券啊主播',                         'ask_coupon',   2, 'AI',      0.97),
(1, 7,  '柠檬不萌',     '库存还有多少？会不会抢不到',                 'ask_stock',    2, 'AI',      0.93),
(1, 10, '奶茶三分糖',   '主播讲得太专业了！',                         'general',      3, 'AI',      0.88),
(1, 8,  '咖啡不加糖',   '敏感肌可以用吗烟酰胺',                       'faq_product',  2, 'HUMAN',   0.96),
(1, 11, '阳光正好',     '这支口红多少钱？',                           'ask_price',    1, 'AI',      0.98),
(1, 7,  '柠檬不萌',     '快递发什么？多久能到',                       'logistics',    2, 'HUMAN',   0.91),
(1, 9,  '爱美的猫',     '上次买的那个面霜过敏可以退吗',               'aftersale',    1, 'HUMAN',   0.94),
(1, 10, '奶茶三分糖',   '有没有满减',                                 'ask_coupon',   2, 'AI',      0.97),
(1, 8,  '咖啡不加糖',   '哈哈哈哈哈哈主播好逗',                       'general',      3, 'FILTERED',0.85),
(1, 11, '阳光正好',     '色号正红适合黄皮吗',                         'faq_product',  2, 'AI',      0.93),
(1, 7,  '柠檬不萌',     '这个价格是直播间专属吗',                     'ask_price',    1, 'AI',      0.95),
(1, 9,  '爱美的猫',     '求上链接！！！',                              'general',      3, 'AI',      0.90),
(1, 10, '奶茶三分糖',   '有没有小样送',                               'faq_policy',   2, 'AI',      0.92),
(1, 8,  '咖啡不加糖',   '主播今天用的什么粉底',                       'faq_product',  2, 'AI',      0.94),
(1, 11, '阳光正好',     '投诉上次买的东西发货太慢',                   'complaint',    1, 'HUMAN',   0.98),
(1, 7,  '柠檬不萌',     '777777',                                     'spam',         3, 'FILTERED',0.72),
(1, 9,  '爱美的猫',     '保湿精华适合冬天用吗',                       'faq_product',  2, 'AI',      0.93),
(1, 10, '奶茶三分糖',   '第二件半价有没有',                           'ask_coupon',   2, 'AI',      0.96),
(1, 8,  '咖啡不加糖',   '主播声音好好听',                             'general',      3, 'AI',      0.90),
(1, 11, '阳光正好',     '这个眼霜对黑眼圈有效吗',                     'faq_product',  2, 'AI',      0.95),
(1, 7,  '柠檬不萌',     '我是干皮求推荐',                             'faq_product',  2, 'AI',      0.91),
(1, 9,  '爱美的猫',     '下单了！主播辛苦了',                         'general',      3, 'AI',      0.92),
(1, 10, '奶茶三分糖',   '有没有积分',                                 'faq_policy',   2, 'AI',      0.89),
(1, 8,  '咖啡不加糖',   '这个身体乳香不香',                           'faq_product',  2, 'AI',      0.94),
(1, 11, '阳光正好',     '能不能便宜点呀',                             'ask_price',    1, 'PENDING', 0.88),
(1, 7,  '柠檬不萌',     '这款和XX品牌比怎么样',                       'faq_product',  2, 'AI',      0.90),
(1, 9,  '爱美的猫',     '主播有没有用同款','faq_product',2,'AI',0.93),
(1, 10, '奶茶三分糖',   '能走顺丰吗',                                 'logistics',    2, 'HUMAN',   0.92),
(1, 8,  '咖啡不加糖',   '售后怎么样',                                 'faq_policy',   2, 'AI',      0.95),
(1, 11, '阳光正好',     '发货地址在哪里',                             'logistics',    2, 'PENDING', 0.90),
(1, 7,  '柠檬不萌',     '这个面膜补水吗',                             'faq_product',  2, 'AI',      0.92),
(1, 9,  '爱美的猫',     '有没有直播专属价',                           'ask_price',    1, 'AI',      0.94),
(1, 10, '奶茶三分糖',   '再唱首歌吧主播',                             'general',      3, 'AI',      0.88),
(1, 8,  '咖啡不加糖',   '支持七天无理由吗',                           'faq_policy',   2, 'AI',      0.96),
(1, 11, '阳光正好',     '色号太暗了能换吗',                           'aftersale',    1, 'HUMAN',   0.94),
(1, 7,  '柠檬不萌',     '这个真的好用吗','faq_product',2,'AI',0.91),
(1, 9,  '爱美的猫',     '求发优惠券！！','ask_coupon',2,'AI',0.98),
(1, 10, '奶茶三分糖',   '老板大气！',                                 'general',      3, 'AI',      0.90),
(1, 8,  '咖啡不加糖',   '有没有包邮',                                 'faq_policy',   2, 'AI',      0.95),
(1, 11, '阳光正好',     '我上次的订单还没收到','logistics',2,'HUMAN',0.96),
(1, 7,  '柠檬不萌',     '油皮适合这个吗',                             'faq_product',  2, 'AI',      0.92),
(1, 9,  '爱美的猫',     '有赠品吗','faq_policy',2,'AI',0.93),
(1, 10, '奶茶三分糖',   '主播下一场什么时候',                         'faq_policy',   2, 'AI',      0.91),
(1, 8,  '咖啡不加糖',   '666666',                                     'general',      3, 'AI',      0.87),
(1, 11, '阳光正好',     '这个价格会变吗','ask_price',1,'AI',0.94),
(1, 7,  '柠檬不萌',     '今天就下单一瓶试试',                         'general',      3, 'AI',      0.90),
(1, 9,  '爱美的猫',     '投诉这个主播卖假货','complaint',1,'HUMAN',0.99),
(1, 10, '奶茶三分糖',   '有没有姐妹和我一起拼单',                     'general',      3, 'AI',      0.89),
(1, 8,  '咖啡不加糖',   '这款成分安全吗','faq_product',2,'AI',0.95),
(1, 11, '阳光正好',     '保质期多久','faq_product',2,'AI',0.94),
(1, 7,  '柠檬不萌',     '有没有其他色号','faq_product',2,'AI',0.93),
(1, 9,  '爱美的猫',     '我先去付款了啊主播','general',3,'AI',0.90),
(1, 10, '奶茶三分糖',   '价格好美丽','general',3,'AI',0.88),
(1, 8,  '咖啡不加糖',   '我买过了真的好用','general',3,'AI',0.91),
(1, 11, '阳光正好',     '主播推荐一下适合学生党的面膜','faq_product',2,'AI',0.93),

-- ===== living session 2 (家居场 低流量) 约 45 条 —— 多塞 ask_coupon & general =====
(2, 7, '柠檬不萌',    '主播好呀',                      'general',    3, 'AI',      0.90),
(2, 8, '咖啡不加糖',  '这款空气炸锅容量多大',           'faq_product',2, 'AI',      0.93),
(2, 9, '爱美的猫',    '有没有优惠券啊',                 'ask_coupon', 2, 'AI',      0.97),
(2, 10, '奶茶三分糖',  '优惠力度怎么样呀',               'ask_coupon', 2, 'AI',      0.96),
(2, 11, '阳光正好',    '有满减吗',                       'ask_coupon', 2, 'AI',      0.95),
(2, 7, '柠檬不萌',    '主播能介绍一下这款吗','faq_product',2,'AI',0.92),
(2, 8, '咖啡不加糖',  '好冷清啊直播间',                 'general',    3, 'AI',      0.85),
(2, 9, '爱美的猫',    '有没有新人优惠券','ask_coupon',2,'AI',0.96),
(2, 10, '奶茶三分糖',  '这个是几升的','faq_product',2,'AI',0.94),
(2, 11, '阳光正好',    '有没有其他颜色','faq_product',2,'AI',0.93),
(2, 7, '柠檬不萌',    '优惠能再大一点吗','ask_price',1,'PENDING',0.89),
(2, 8, '咖啡不加糖',  '这款和上一代有什么区别','faq_product',2,'AI',0.91),
(2, 9, '爱美的猫',    '库存还剩多少呀','ask_stock',2,'AI',0.94),
(2, 10, '奶茶三分糖',  '主播辛苦啦',                     'general',    3, 'AI',      0.90),
(2, 11, '阳光正好',    '有优惠券嘛求发','ask_coupon',2,'AI',0.98),
(2, 7, '柠檬不萌',    '能炸整鸡吗','faq_product',2,'AI',0.93),
(2, 8, '咖啡不加糖',  '保修多久','faq_policy',2,'AI',0.95),
(2, 9, '爱美的猫',    '什么时候结束直播','faq_policy',2,'PENDING',0.90),
(2, 10, '奶茶三分糖',  '这款性价比怎么样','faq_product',2,'AI',0.92),
(2, 11, '阳光正好',    '有红包吗','ask_coupon',2,'AI',0.97),
(2, 7, '柠檬不萌',    '有没有赠品','faq_policy',2,'AI',0.93),
(2, 8, '咖啡不加糖',  '这个价格是直播间才有吗','ask_price',1,'AI',0.95),
(2, 9, '爱美的猫',    '下单后多久发货','logistics',2,'PENDING',0.91),
(2, 10, '奶茶三分糖',  '我先看看再说','general',3,'AI',0.88),
(2, 11, '阳光正好',    '有没有老客户专享','ask_coupon',2,'AI',0.95),
(2, 7, '柠檬不萌',    '噪音大吗','faq_product',2,'AI',0.93),
(2, 8, '咖啡不加糖',  '能不能开发票','faq_policy',2,'AI',0.94),
(2, 9, '爱美的猫',    '有运费险吗','faq_policy',2,'AI',0.96),
(2, 10, '奶茶三分糖',  '主播声音真好听','general',3,'AI',0.90),
(2, 11, '阳光正好',    '有没有第二件半价','ask_coupon',2,'AI',0.96),
(2, 7, '柠檬不萌',    '这款电饭煲煮饭好吃吗','faq_product',2,'AI',0.94),
(2, 8, '咖啡不加糖',  '支持以旧换新吗','faq_policy',2,'AI',0.92),
(2, 9, '爱美的猫',    '优惠券还有吗','ask_coupon',2,'AI',0.97),
(2, 10, '奶茶三分糖',  '客服在哪联系','faq_policy',2,'PENDING',0.90),
(2, 11, '阳光正好',    '有活动补贴吗','ask_coupon',2,'AI',0.94),
(2, 7, '柠檬不萌',    '看起来不错','general',3,'AI',0.88),
(2, 8, '咖啡不加糖',  '功率多大','faq_product',2,'AI',0.93),
(2, 9, '爱美的猫',    '有没有满减券','ask_coupon',2,'AI',0.97),
(2, 10, '奶茶三分糖',  '好的我再想想','general',3,'AI',0.85),
(2, 11, '阳光正好',    '这个价格能接受','general',3,'AI',0.87),
(2, 7, '柠檬不萌',    '保修怎么弄','faq_policy',2,'AI',0.93),
(2, 8, '咖啡不加糖',  '可以预约吗','faq_product',2,'AI',0.94),
(2, 9, '爱美的猫',    '还有优惠券吗求求了','ask_coupon',2,'AI',0.98),
(2, 10, '奶茶三分糖',  '主播加油','general',3,'AI',0.90),
(2, 11, '阳光正好',    '我也想要一张优惠券','ask_coupon',2,'AI',0.97);

-- ============================
-- agent_action —— 对应 danmaku 若干条
-- model 用 qwen-plus / doubao-pro 等
-- ============================
INSERT INTO agent_action (session_id, msg_id, tool_name, tool_args, tool_result, decision_reason, latency_ms, model_used, token_cost, operator_id) VALUES
-- session 1 的 agent actions
(1, 3,  'issue_coupon', '{"coupon_id":1,"target_user_id":9}', '成功向用户ID=9发放优惠券1', '用户索要优惠券，路由COUPON', 280, 'qwen-plus', 250, NULL),
(1, 4,  'query_stock',  '{"sku_id":7}',                           'sku_id=7 当前库存: 8 件',    '用户问库存，路由STOCK',      195, 'qwen-plus', 180, NULL),
(1, 6,  'send_danmaku_reply', '{"reply":"烟酰胺建议先从低浓度开始，敏感肌可搭配保湿精华"}', '弹幕已发送', '敏感肌使用建议，路由FAQ', 310, 'qwen-plus', 320, NULL),
(1, 7,  'send_danmaku_reply', '{"reply":"正红口红直播间专属价168元，原价228"}', '弹幕已发送', '查询价格，路由FAQ', 240, 'qwen-plus', 200, NULL),
(1, 8,  'create_human_ticket', '{"intent":"logistics","priority":"medium"}', '工单已创建', '物流问题需人工处理，路由HUMAN', 180, 'qwen-plus', 150, NULL),
(1, 9,  'create_human_ticket', '{"intent":"aftersale","priority":"high"}', '工单已创建', '售后退货，路由HUMAN', 170, 'qwen-plus', 160, NULL),
(1, 10, 'issue_coupon', '{"coupon_id":2,"target_user_id":10}', '成功向用户ID=10发放优惠券2', '用户问满减，路由COUPON', 260, 'qwen-plus', 240, NULL),
(1, 11, 'send_danmaku_reply', '{"reply":"已过滤垃圾弹幕: 哈哈哈哈哈哈主播好逗"}', '弹幕已过滤', '垃圾弹幕识别，路由FILTER', 150, 'doubao-pro', 100, NULL),
(1, 12, 'send_danmaku_reply', '{"reply":"正红色号非常适合黄皮，是不挑皮的正宫红"}', '弹幕已发送', '产品咨询，路由FAQ', 220, 'qwen-plus', 210, NULL),
(1, 16, 'send_danmaku_reply', '{"reply":"主播今天使用的是悦颜持妆粉底液自然色号~"}', '弹幕已发送', '主播同款查询，路由FAQ', 230, 'qwen-plus', 190, NULL),
(1, 17, 'create_human_ticket', '{"intent":"complaint","priority":"high"}', '工单已创建', '发货投诉，路由HUMAN', 160, 'qwen-plus', 140, 3),
(1, 19, 'send_danmaku_reply', '{"reply":"保湿精华冬天非常适合，锁水效果一流"}', '弹幕已发送', '产品咨询，路由FAQ', 210, 'qwen-plus', 200, NULL),
(1, 20, 'issue_coupon', '{"coupon_id":1,"target_user_id":10}', '成功发放15%折扣券', '索要第二件半价，发放可叠加券', 250, 'qwen-plus', 230, NULL),
-- session 2 的 agent actions (ask_coupon 密集)
(2, 3,  'issue_coupon', '{"coupon_id":4,"target_user_id":9}', '成功向用户ID=9发放优惠券4', '用户索要优惠券', 270, 'qwen-plus', 260, NULL),
(2, 4,  'issue_coupon', '{"coupon_id":4,"target_user_id":10}', '成功发放10%折扣券', '问优惠力度', 265, 'qwen-plus', 250, NULL),
(2, 5,  'issue_coupon', '{"coupon_id":5,"target_user_id":11}', '成功发放满299减50券', '问满减', 280, 'qwen-plus', 255, NULL),
(2, 7,  'issue_coupon', '{"coupon_id":4,"target_user_id":9}', '成功发放新人优惠券', '新人优惠券', 290, 'qwen-plus', 265, NULL),
(2, 11, 'query_stock', '{"sku_id":23}', 'sku_id=23(空气炸锅5L) 当前库存: 120 件', '用户问库存', 200, 'qwen-plus', 185, NULL),
(2, 13, 'issue_coupon', '{"coupon_id":4,"target_user_id":11}', '成功发放', '又索要优惠券', 275, 'qwen-plus', 260, NULL),
(2, 18, 'create_human_ticket', '{"intent":"logistics","priority":"medium"}', '工单已创建', '物流发货时间，路由HUMAN', 175, 'qwen-plus', 155, NULL),
(2, 20, 'issue_coupon', '{"coupon_id":4,"target_user_id":11}', '成功发放满减券', '红包优惠券', 280, 'qwen-plus', 258, NULL),
(2, 23, 'create_human_ticket', '{"intent":"faq_policy","priority":"low"}', '工单已创建', '客服入口不明，人工介入', 165, 'qwen-plus', 145, NULL);

-- ============================
-- monitor_event
-- ============================
INSERT INTO monitor_event (session_id, event_type, metric_value, threshold, agent_response, status, created_at) VALUES
-- living 场1: stock_alert 对应 sku_id=7 (氨基酸洁面乳旅行装 stock=8)
(1, 'stock_alert',     8.00,    15.00,    '已触发库存预警：氨基酸洁面乳旅行装(sku_id=7)仅剩8件，低于阈值15', 'notified', NOW()),
-- living 场1: peak_focus 峰值关注
(1, 'peak_focus',      125.00,  100.00,   '主推款产品(sku_id=7)弹幕提及量激增，建议立即讲解', 'acted',    NOW()),
-- living 场2: low_conversion 低转化
(2, 'low_conversion',  0.0200,  0.0500,   '当前转化率仅2%，低于阈值5%，建议发放专属优惠券提升转化', 'notified', NOW()),
-- 历史：session 3 viewer_drop
(3, 'viewer_drop',     -0.35,   -0.20,    '30分钟内观众流失率35%，建议发放红包', 'acted',    DATE_SUB(NOW(), INTERVAL 2 DAY)),
-- 历史：session 10 peak_focus
(10, 'peak_focus',     210.00,  150.00,   '主推产品弹幕提及峰值210', 'acted',    DATE_SUB(NOW(), INTERVAL 3 DAY));

-- ============================
-- sales_order  (order_id 形如 SO+yyyymmdd+6位序号)
-- living 场1 20+ 订单，living 场2 仅 3 条
-- 为 GMV 下滑场景：过去3天 store_id=1 revenue_daily 某一天骤降60%
-- ============================
INSERT INTO sales_order (order_id, session_id, store_id, user_id, coupon_id, total_amount, pay_amount, discount_amount, status, channel, create_time, pay_time) VALUES
-- ===== session 1 living 美妆场 22 条 =====
('SO20261022000001', 1, 1, 7,  1, 128.00, 108.80, 19.20, '01', 'LIVE', NOW(), NULL),
('SO20261022000002', 1, 1, 8,  2, 299.00, 269.00, 30.00, '02', 'LIVE', NOW(), NOW()),
('SO20261022000003', 1, 1, 9,  3, 168.00, 168.00, 0.00,  '01', 'LIVE', NOW(), NULL),
('SO20261022000004', 1, 1, 10, 1, 198.00, 168.30, 29.70, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 40 MINUTE), DATE_SUB(NOW(), INTERVAL 35 MINUTE)),
('SO20261022000005', 1, 1, 11, 2, 326.00, 296.00, 30.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 38 MINUTE), DATE_SUB(NOW(), INTERVAL 33 MINUTE)),
('SO20261022000006', 1, 1, 7,  NULL, 168.00, 168.00, 0.00, '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 35 MINUTE), NULL),
('SO20261022000007', 1, 1, 8,  1, 256.00, 217.60, 38.40, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 32 MINUTE), DATE_SUB(NOW(), INTERVAL 32 MINUTE)),
('SO20261022000008', 1, 1, 9,  2, 499.00, 469.00, 30.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 30 MINUTE), DATE_SUB(NOW(), INTERVAL 28 MINUTE)),
('SO20261022000009', 1, 1, 10, 3, 58.00, 58.00, 0.00,  '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 28 MINUTE), NULL),
('SO20261022000010', 1, 1, 11, 1, 216.00, 183.60, 32.40, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 26 MINUTE), DATE_SUB(NOW(), INTERVAL 24 MINUTE)),
('SO20261022000011', 1, 1, 7,  2, 336.00, 306.00, 30.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 24 MINUTE), DATE_SUB(NOW(), INTERVAL 22 MINUTE)),
('SO20261022000012', 1, 1, 8,  NULL, 78.00, 78.00, 0.00, '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 22 MINUTE), NULL),
('SO20261022000013', 1, 1, 9,  1, 156.00, 132.60, 23.40, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 20 MINUTE), DATE_SUB(NOW(), INTERVAL 18 MINUTE)),
('SO20261022000014', 1, 1, 10, 2, 299.00, 269.00, 30.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 18 MINUTE), DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
('SO20261022000015', 1, 1, 11, 3, 168.00, 168.00, 0.00, '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 16 MINUTE), NULL),
('SO20261022000016', 1, 1, 7,  1, 128.00, 108.80, 19.20, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 14 MINUTE), DATE_SUB(NOW(), INTERVAL 12 MINUTE)),
('SO20261022000017', 1, 1, 8,  2, 299.00, 269.00, 30.00, '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 12 MINUTE), NULL),
('SO20261022000018', 1, 1, 9,  NULL, 268.00, 268.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 10 MINUTE), DATE_SUB(NOW(), INTERVAL 8 MINUTE)),
('SO20261022000019', 1, 1, 10, 1, 198.00, 168.30, 29.70, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 8 MINUTE), DATE_SUB(NOW(), INTERVAL 6 MINUTE)),
('SO20261022000020', 1, 1, 11, 2, 459.00, 429.00, 30.00, '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 6 MINUTE), NULL),
('SO20261022000021', 1, 1, 7,  1, 168.00, 142.80, 25.20, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 4 MINUTE), DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
('SO20261022000022', 1, 1, 8,  3, 58.00, 58.00, 0.00,  '01', 'LIVE', DATE_SUB(NOW(), INTERVAL 2 MINUTE), NULL),
-- ===== session 2 living 家居场 仅 3 条 =====
('SO20261022000023', 2, 5, 7,  4, 399.00, 359.10, 39.90, '01', 'LIVE', NOW(), NULL),
('SO20261022000024', 2, 5, 8,  NULL, 159.00, 159.00, 0.00, '02', 'LIVE', NOW(), NOW()),
('SO20261022000025', 2, 5, 9,  5, 399.00, 349.00, 50.00, '02', 'LIVE', NOW(), NOW()),
-- ===== session 3 已结束 =====
('SO20261021000001', 3, 2, 7,  NULL, 899.00, 899.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),
('SO20261021000002', 3, 2, 8,  NULL, 299.00, 299.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),
('SO20261021000003', 3, 2, 9,  NULL, 128.00, 128.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 2 DAY), DATE_SUB(NOW(), INTERVAL 2 DAY)),
-- ===== session 4 已结束 =====
('SO20261020000001', 4, 3, 7,  NULL, 59.00, 59.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
('SO20261020000002', 4, 3, 8,  NULL, 299.00, 299.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY)),
-- ===== session 5 已结束 =====
('SO20261021000004', 5, 4, 7,  NULL, 799.00, 799.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),
('SO20261021000005', 5, 4, 8,  NULL, 199.00, 199.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY)),
-- ===== session 9 store_id=1 过去 3 天里 —— 用于 GMV 下滑场景 =====
('SO20261019000001', 9, 9, 7,  NULL, 168.00, 168.00, 0.00, '02', 'LIVE', DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY));

-- ============================
-- sales_order_detail
-- ============================
INSERT INTO sales_order_detail (order_id, sku_id, product_name, spec, price, qty, subtotal, coupon_applied) VALUES
('SO20261022000001', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 1),
('SO20261022000002', 15, '持妆粉底液 #自然色', '30ml',        299.00, 1, 299.00, 1),
('SO20261022000003', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 0),
('SO20261022000004', 3,  '烟酰胺美白祛斑精华', '30ml',        198.00, 1, 198.00, 1),
('SO20261022000005', 15, '持妆粉底液 #自然色', '30ml',        299.00, 1, 299.00, 1),
('SO20261022000005', 6,  '氨基酸洁面乳',       '120g 正装',   58.00,  1, 58.00, 0),
('SO20261022000006', 7,  '氨基酸洁面乳',       '30g 旅行装',  19.90,  1, 19.90, 0),
('SO20261022000006', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 0),
('SO20261022000007', 5,  '视黄醇抗老眼霜',     '20g',         268.00, 1, 268.00, 1),
('SO20261022000008', 28, '智能电饭煲',         '4L 厚釜',     499.00, 1, 499.00, 1),
('SO20261022000009', 6,  '氨基酸洁面乳',       '120g 正装',   58.00,  1, 58.00, 0),
('SO20261022000010', 3,  '烟酰胺美白祛斑精华', '30ml',        198.00, 1, 198.00, 1),
('SO20261022000010', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 0),
('SO20261022000011', 9,  '神经酰胺修护面霜',   '50g',         258.00, 1, 258.00, 1),
('SO20261022000011', 14, '水光唇釉 #番茄红',   '6g',          128.00, 1, 128.00, 0),
('SO20261022000012', 17, '散粉定妆粉 透明色',  '10g',         88.00,  1, 88.00,  0),
('SO20261022000013', 1,  '玻尿酸保湿精华液',   '30ml',        128.00, 1, 128.00, 1),
('SO20261022000013', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 0),
('SO20261022000014', 15, '持妆粉底液 #自然色', '30ml',        299.00, 1, 299.00, 1),
('SO20261022000015', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 0),
('SO20261022000016', 1,  '玻尿酸保湿精华液',   '30ml',        128.00, 1, 128.00, 1),
('SO20261022000017', 15, '持妆粉底液 #自然色', '30ml',        299.00, 1, 299.00, 1),
('SO20261022000018', 5,  '视黄醇抗老眼霜',     '20g',         268.00, 1, 268.00, 0),
('SO20261022000019', 3,  '烟酰胺美白祛斑精华', '30ml',        198.00, 1, 198.00, 1),
('SO20261022000020', 26, '电压力锅',           '5L 曜石黑',   459.00, 1, 459.00, 1),
('SO20261022000021', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 1),
('SO20261022000022', 6,  '氨基酸洁面乳',       '120g 正装',   58.00,  1, 58.00,  0),
('SO20261022000023', 23, '纳米空气炸锅 Pro',   '5L 银色',     399.00, 1, 399.00, 1),
('SO20261022000024', 34, '收纳箱 6件套',       '中号',        159.00, 1, 159.00, 0),
('SO20261022000025', 28, '智能电饭煲',         '4L 厚釜',     499.00, 1, 499.00, 1),
('SO20261021000001', 35, '降噪蓝牙耳机 X7',     '曜石黑',      899.00, 1, 899.00, 0),
('SO20261021000002', 42, '智能运动手表 S2',     '黑',          799.00, 1, 799.00, 0),
('SO20261021000003', 46, '65W氮化镓快充',      '三口同充',    128.00, 1, 128.00, 0),
('SO20261020000001', 51, '低温冷萃咖啡胶囊',   '12粒',        59.00,  1, 59.00,  0),
('SO20261020000002', 56, '每日坚果 30袋装',     '6种坚果',     89.00,  3, 267.00, 0),
('SO20261021000004', 35, '降噪蓝牙耳机 X7',     '曜石黑',      899.00, 1, 899.00, 0),
('SO20261021000005', 44, '健康监测手环',       'B6 手环',     199.00, 1, 199.00, 0),
('SO20261019000001', 10, '丝绒哑光口红 #正红',  '3.5g',        168.00, 1, 168.00, 0);

-- ============================
-- payment_record
-- ============================
INSERT INTO payment_record (order_id, amount, channel, status, pay_time) VALUES
('SO20261022000001', 108.80, 'ALIPAY', 'success', NOW()),
('SO20261022000002', 269.00, 'ALIPAY', 'success', NOW()),
('SO20261022000003', 168.00, 'WECHAT', 'success', NOW()),
('SO20261022000004', 168.30, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 35 MINUTE)),
('SO20261022000005', 296.00, 'WECHAT', 'success', DATE_SUB(NOW(), INTERVAL 33 MINUTE)),
('SO20261022000006', 168.00, 'ALIPAY', 'success', NOW()),
('SO20261022000007', 217.60, 'ALIPAY', 'failed',  DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
('SO20261022000008', 469.00, 'WECHAT', 'success', DATE_SUB(NOW(), INTERVAL 28 MINUTE)),
('SO20261022000009', 58.00,  'WECHAT', 'success', NOW()),
('SO20261022000010', 183.60, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 24 MINUTE)),
('SO20261022000011', 306.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 22 MINUTE)),
('SO20261022000012', 78.00,  'WECHAT', 'success', NOW()),
('SO20261022000013', 132.60, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 18 MINUTE)),
('SO20261022000014', 269.00, 'WECHAT', 'success', DATE_SUB(NOW(), INTERVAL 15 MINUTE)),
('SO20261022000015', 168.00, 'ALIPAY', 'success', NOW()),
('SO20261022000016', 108.80, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 12 MINUTE)),
('SO20261022000017', 269.00, 'WECHAT', 'success', NOW()),
('SO20261022000018', 268.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 8 MINUTE)),
('SO20261022000019', 168.30, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 6 MINUTE)),
('SO20261022000020', 429.00, 'WECHAT', 'success', NOW()),
('SO20261022000021', 142.80, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 2 MINUTE)),
('SO20261022000022', 58.00,  'WECHAT', 'success', NOW()),
('SO20261022000023', 359.10, 'ALIPAY', 'success', NOW()),
('SO20261022000024', 159.00, 'ALIPAY', 'success', NOW()),
('SO20261022000025', 349.00, 'WECHAT', 'success', NOW()),
('SO20261021000001', 899.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 2 DAY)),
('SO20261021000002', 299.00, 'WECHAT', 'success', DATE_SUB(NOW(), INTERVAL 2 DAY)),
('SO20261021000003', 128.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 2 DAY)),
('SO20261020000001', 59.00,  'WECHAT', 'success', DATE_SUB(NOW(), INTERVAL 3 DAY)),
('SO20261020000002', 299.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 3 DAY)),
('SO20261021000004', 799.00, 'WECHAT', 'success', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('SO20261021000005', 199.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('SO20261019000001', 168.00, 'ALIPAY', 'success', DATE_SUB(NOW(), INTERVAL 3 DAY));

-- ============================
-- revenue_daily
-- 场景：store_id=1 (上海星耀广场) 过去3天 —— 某一天骤降 60%
-- 基线：
--   2026-10-21: 31200.00  (正常)
--   2026-10-20: 34500.00  (正常)
--   2026-10-19: 13800.00  (骤降 60%！触发 GMV 下滑告警)
--   2026-10-22: 22313.00  (当前 living 场 进行中，实时)
-- ============================
INSERT INTO revenue_daily (store_id, session_id, date, revenue, orders, avg_ticket, conversion_rate) VALUES
-- store_id=1 上海星耀广场
(1, 1,  DATE_SUB(CURDATE(), INTERVAL 1 DAY), 31200.00, 86, 362.79, 0.0820),
(1, NULL, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 34500.00, 95, 363.16, 0.0910),
(1, NULL, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 13800.00, 38, 363.16, 0.0360),  -- 骤降 60%
(1, 1,  CURDATE(),                            22313.00, 22, 1014.23, 0.0417),
-- store_id=2 北京中心城
(2, 3,  DATE_SUB(CURDATE(), INTERVAL 1 DAY), 108000.00, 238, 453.78, 0.0980),
(2, NULL, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 89000.00, 201, 442.79, 0.0870),
(2, NULL, DATE_SUB(CURDATE(), INTERVAL 3 DAY), 76500.00, 176, 434.66, 0.0790),
(2, 14, DATE_SUB(CURDATE(), INTERVAL 1 DAY),  52300.00, 118, 443.22, 0.0910),
-- store_id=5 杭州银泰城
(5, 2,  CURDATE(),                            863.10,   3, 287.70, 0.0200),  -- 低流量场
(5, NULL, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 21000.00, 52, 403.85, 0.0730),
(5, NULL, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 18900.00, 47, 402.13, 0.0680),
-- store_id=3 广州
(3, 4,  DATE_SUB(CURDATE(), INTERVAL 3 DAY), 42500.00, 128, 332.03, 0.0890),
(3, NULL, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 45800.00, 138, 331.88, 0.0920),
-- store_id=4 深圳
(4, 5,  DATE_SUB(CURDATE(), INTERVAL 1 DAY), 23800.00, 58, 410.34, 0.0680),
(4, NULL, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 26500.00, 63, 420.63, 0.0720),
-- store_id=9 西安
(9, 9,  DATE_SUB(CURDATE(), INTERVAL 3 DAY), 27800.00, 74, 375.68, 0.0610),
(9, NULL, DATE_SUB(CURDATE(), INTERVAL 2 DAY), 30200.00, 81, 372.84, 0.0650);

-- ============================
-- kb_doc 20+ 条
-- ============================
INSERT INTO kb_doc (category, chunk_text, source, milvus_id) VALUES
-- 商品知识
('商品知识', '玻尿酸保湿精华液采用大、小、微三种分子量玻尿酸复配，大分子量在肌肤表面形成锁水膜，小分子量渗透角质层，微分子直达真皮层。主要成分：玻尿酸、甘油、丁二醇。适合油皮、混油皮及所有肤质。', '产品手册-保湿系列', NULL),
('商品知识', '烟酰胺美白祛斑精华采用5%高纯度烟酰胺浓度，搭配1%神经酰胺修护屏障，同时促进胶原蛋白生成，温和提亮肤色淡化色斑。建议先建立耐受，隔天使用。', '产品手册-美白系列', NULL),
('商品知识', '视黄醇抗老眼霜采用0.5%缓释视黄醇+咖啡因+烟酰胺配方，三重功效：对抗细纹、减轻黑眼圈、消除眼部浮肿。注意避光使用，建议夜间使用。', '产品手册-抗老系列', NULL),
('商品知识', '氨基酸洁面乳使用纯氨基酸表活，PH值5.5接近肌肤天然PH值，温和清洁不破坏屏障。敏感肌、孕妇均可使用。', '产品手册-基础护理', NULL),
('商品知识', '丝绒哑光口红主打显色浓郁、持久不脱妆、不拔干三大卖点。颜色覆盖正红、玫瑰红、豆沙色等热门色系，喝水不沾杯。', '产品手册-彩妆系列', NULL),
('商品知识', '纳米空气炸锅Pro容量5L，采用纳米陶瓷不沾内胆，360°热风循环加热，一键脆皮功能。最高温度200°C，可炸鸡、烤串、做蛋糕。', '产品手册-厨房电器', NULL),
('商品知识', '降噪蓝牙耳机X7行业领先-42dB主动降噪，支持Hi-Res小金标认证，40小时超长续航。蓝牙5.3连接稳定，支持多点连接。', '产品手册-数码产品', NULL),
('商品知识', '低温冷萃咖啡胶囊采用12小时低温冷萃工艺，保留阿拉比卡咖啡豆原始风味，醇厚回甘。兼容多种胶囊咖啡机。', '产品手册-食品饮料', NULL),

-- 话术库
('话术库', '欢迎语：大家好，欢迎来到直播间！我是主播林小美，今天给大家带来双11美妆专场，主播手上的王牌产品是玻尿酸保湿精华液，原价168，今天直播间只要多少钱？让我们拭目以待！', '主播话术规范', NULL),
('话术库', '秒杀引导：倒计时3、2、1，上链接！喜欢的宝宝赶紧拍，库存有限，抢完就没啦！这个价格今天只有直播间才有，错过等一年！', '主播话术规范', NULL),
('话术库', '痛点共鸣：有没有宝宝冬天一化妆就卡粉？有没有和我一样是敏感肌不敢随便用护肤品的？今天这款氨基酸洁面乳就是为你们准备的！', '主播话术规范', NULL),
('话术库', '逼单话术：主播跟工厂砍了三个月才拿到这个价格，库存只剩最后200件了！拍下48小时内发货，顺丰包邮，支持七天无理由退换！', '主播话术规范', NULL),
('话术库', '拉新话术：新进来的宝宝先点个关注，左上角福袋马上开奖，关注主播就能参与抽奖！今天整场直播抽3波福袋，奖品都是直播间的热门产品！', '主播话术规范', NULL),

-- 政策
('政策', '退换货政策：所有商品支持签收后7天无理由退换，需保证商品未拆封、吊牌完整。特殊商品如化妆品已拆封试用不支持退换。人为损坏不在退换范围内。', '售后政策手册', NULL),
('政策', '发货时效：普通订单48小时内发货，大促期间延长至72小时。偏远地区或节假日可能略有延迟。默认顺丰快递，可补差价发冷链。', '物流政策手册', NULL),
('政策', '优惠券使用规则：优惠券分为满减券、折扣券、包邮券三种。满减券需满足最低消费金额，折扣券不可叠加使用，包邮券仅限国内订单。优惠券有效期24小时，过期自动失效。', '营销政策手册', NULL),
('政策', '会员积分规则：每消费1元积1分，100积分可抵扣1元。积分有效期至次年12月31日。会员等级分为银卡、金卡、钻石卡，享受不同比例积分加成。', '会员政策手册', NULL),

-- 历史FAQ
('历史FAQ', 'Q: 这款精华适合油皮吗？A: 这款玻尿酸精华分大中小三种分子量，油皮建议夏天用清爽款，冬天用滋润款，具体看个人肤质和所在城市气候。', '历史FAQ-美妆-2026Q3', NULL),
('历史FAQ', 'Q: 敏感肌可以用烟酰胺吗？A: 可以建议先从低浓度开始（2%），逐步建立耐受。如果刺痛或泛红请停用并保湿修护。推荐搭配神经酰胺产品使用。', '历史FAQ-美妆-2026Q3', NULL),
('历史FAQ', 'Q: 空气炸锅能做什么？A: 可以炸鸡、烤串、做蛋糕、烤红薯，所有需要无油或少油炸的菜品都能做。5L容量适合4-5口之家。', '历史FAQ-家居-2026Q3', NULL),
('历史FAQ', 'Q: 降噪耳机续航多久？A: X7开启降噪后续航约30小时，关闭降噪可达40小时。充电10分钟可使用5小时。支持Type-C快充。', '历史FAQ-数码-2026Q3', NULL),
('历史FAQ', 'Q: 优惠券能叠加吗？A: 不同类型优惠券不可叠加使用，但可以和直播间专属价叠加。单笔订单限用一张优惠券。', '历史FAQ-活动-2026Q4', NULL),
('历史FAQ', 'Q: 物流发什么快递？多久到？A: 默认顺丰速运，一线城市次日达，二线城市2-3天，偏远地区3-5天。', '历史FAQ-物流-2026Q4', NULL);

-- 门店商品覆盖：每家门店随机覆盖约 70% 的商品，库存按门店/商品确定性生成
INSERT IGNORE INTO store_product (store_id, product_id, stock)
SELECT s.store_id, p.product_id, 20 + MOD(s.store_id * 7 + p.product_id * 13, 80)
FROM store s CROSS JOIN product p
WHERE MOD(s.store_id + p.product_id, 10) < 7;

SET FOREIGN_KEY_CHECKS = 1;
