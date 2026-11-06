SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ========== store ==========
CREATE TABLE IF NOT EXISTS store (
    store_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    city VARCHAR(32) NOT NULL,
    address VARCHAR(255),
    manager VARCHAR(64),
    status TINYINT DEFAULT 1 COMMENT '1营业 0停业',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店';

-- ========== auth_user ==========
CREATE TABLE IF NOT EXISTS auth_user (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(32),
    role ENUM('CUSTOMER','OPERATOR','HOST','ADMIN') DEFAULT 'CUSTOMER',
    status TINYINT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='认证用户';

-- ========== staff ==========
CREATE TABLE IF NOT EXISTS staff (
    staff_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    store_id BIGINT NOT NULL,
    user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(64) NOT NULL,
    role ENUM('MANAGER','HOST','OPERATOR') NOT NULL,
    availability VARCHAR(255),
    status ENUM('online','offline','busy') DEFAULT 'online',
    max_concurrent INT DEFAULT 5,
    CONSTRAINT fk_staff_store FOREIGN KEY (store_id) REFERENCES store(store_id),
    CONSTRAINT fk_staff_user FOREIGN KEY (user_id) REFERENCES auth_user(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店员工';

-- ========== product_category ==========
CREATE TABLE IF NOT EXISTS product_category (
    category_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_id BIGINT NULL,
    name VARCHAR(64) NOT NULL,
    level INT DEFAULT 1,
    sort_order INT DEFAULT 0,
    is_show TINYINT DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品分类';

-- ========== product ==========
CREATE TABLE IF NOT EXISTS product (
    product_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    category_id BIGINT NOT NULL,
    product_name VARCHAR(128) NOT NULL,
    subtitle VARCHAR(255),
    brand VARCHAR(64),
    main_image VARCHAR(255),
    description TEXT,
    status TINYINT DEFAULT 1,
    sales_count INT DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES product_category(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品';

-- ========== sku_info ==========
CREATE TABLE IF NOT EXISTS sku_info (
    sku_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    product_id BIGINT NOT NULL,
    sku_code VARCHAR(64) UNIQUE NOT NULL,
    spec VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),
    stock INT DEFAULT 0,
    image VARCHAR(255),
    CONSTRAINT fk_sku_product FOREIGN KEY (product_id) REFERENCES product(product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='商品SKU';

-- ========== live_session ==========
CREATE TABLE IF NOT EXISTS live_session (
    session_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    store_id BIGINT NOT NULL,
    host_id BIGINT NOT NULL,
    title VARCHAR(128) NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NULL,
    status ENUM('planned','living','ended','aborted') DEFAULT 'planned',
    viewer_count INT DEFAULT 0,
    peak_viewer INT DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_live_store FOREIGN KEY (store_id) REFERENCES store(store_id),
    CONSTRAINT fk_live_host FOREIGN KEY (host_id) REFERENCES staff(staff_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间';

-- ========== live_product ==========
CREATE TABLE IF NOT EXISTS live_product (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    sku_id BIGINT NULL,
    explain_status ENUM('pending','explaining','explained') DEFAULT 'pending',
    order_in_session INT DEFAULT 0,
    is_focus TINYINT DEFAULT 0,
    CONSTRAINT fk_lp_session FOREIGN KEY (session_id) REFERENCES live_session(session_id),
    CONSTRAINT fk_lp_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT fk_lp_sku FOREIGN KEY (sku_id) REFERENCES sku_info(sku_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='直播间挂载商品';

-- ========== store_product 门店商品覆盖 ==========
CREATE TABLE IF NOT EXISTS store_product (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    store_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    stock INT DEFAULT 0,
    UNIQUE KEY uk_store_product (store_id, product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='门店在售商品与门店库存';

-- ========== coupon ==========
CREATE TABLE IF NOT EXISTS coupon (
    coupon_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    type ENUM('discount','percent','shipping') NOT NULL,
    threshold DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) NOT NULL,
    stock INT DEFAULT 0,
    issued INT DEFAULT 0,
    valid_start DATETIME,
    valid_end DATETIME,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_coupon_session FOREIGN KEY (session_id) REFERENCES live_session(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='优惠券';

-- ========== coupon_issue ==========
CREATE TABLE IF NOT EXISTS coupon_issue (
    issue_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    coupon_id BIGINT NOT NULL,
    session_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    issued_by ENUM('MANUAL','AGENT') NOT NULL,
    amount_cost DECIMAL(10,2) DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ci_coupon FOREIGN KEY (coupon_id) REFERENCES coupon(coupon_id),
    CONSTRAINT fk_ci_session FOREIGN KEY (session_id) REFERENCES live_session(session_id),
    CONSTRAINT fk_ci_user FOREIGN KEY (user_id) REFERENCES auth_user(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='优惠券发放记录';

-- ========== danmaku ==========
CREATE TABLE IF NOT EXISTS danmaku (
    msg_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    nickname VARCHAR(64),
    content TEXT NOT NULL,
    intent VARCHAR(32),
    priority TINYINT DEFAULT 3,
    handled_by ENUM('AI','HUMAN','PENDING','FILTERED') DEFAULT 'PENDING',
    confidence DECIMAL(3,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id, created_at),
    CONSTRAINT fk_danmaku_session FOREIGN KEY (session_id) REFERENCES live_session(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='弹幕';

-- ========== intent_label ==========
CREATE TABLE IF NOT EXISTS intent_label (
    intent VARCHAR(32) PRIMARY KEY,
    label_name VARCHAR(64) NOT NULL,
    route_to ENUM('FAQ','COUPON','STOCK','HUMAN','FILTER') NOT NULL,
    need_hitl TINYINT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='意图标签';

-- ========== agent_action ==========
CREATE TABLE IF NOT EXISTS agent_action (
    action_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    msg_id BIGINT NULL,
    tool_name VARCHAR(64) NOT NULL,
    tool_args JSON,
    tool_result TEXT,
    decision_reason VARCHAR(255),
    latency_ms INT,
    model_used VARCHAR(64),
    token_cost INT DEFAULT 0,
    operator_id BIGINT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_time (session_id, created_at),
    CONSTRAINT fk_aa_session FOREIGN KEY (session_id) REFERENCES live_session(session_id),
    CONSTRAINT fk_aa_msg FOREIGN KEY (msg_id) REFERENCES danmaku(msg_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体动作';

-- ========== monitor_event ==========
CREATE TABLE IF NOT EXISTS monitor_event (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    event_type ENUM('viewer_drop','stock_alert','low_conversion','peak_focus') NOT NULL,
    metric_value DECIMAL(12,2),
    threshold DECIMAL(12,2),
    agent_response VARCHAR(500),
    status ENUM('notified','acted','ignored') DEFAULT 'notified',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_me_session FOREIGN KEY (session_id) REFERENCES live_session(session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='监控事件';

-- ========== sales_order ==========
CREATE TABLE IF NOT EXISTS sales_order (
    order_id VARCHAR(32) PRIMARY KEY,
    session_id BIGINT NOT NULL,
    store_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    coupon_id BIGINT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    pay_amount DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    status ENUM('01','02','03','07') DEFAULT '01',
    channel ENUM('LIVE','STORE_PICKUP','DOUYIN','KUAISHOU','WECHAT_CHANNEL') DEFAULT 'LIVE',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    pay_time DATETIME NULL,
    CONSTRAINT fk_order_session FOREIGN KEY (session_id) REFERENCES live_session(session_id),
    CONSTRAINT fk_order_store FOREIGN KEY (store_id) REFERENCES store(store_id),
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES auth_user(user_id),
    CONSTRAINT fk_order_coupon FOREIGN KEY (coupon_id) REFERENCES coupon(coupon_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='销售订单';

-- ========== sales_order_detail ==========
CREATE TABLE IF NOT EXISTS sales_order_detail (
    detail_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    sku_id BIGINT,
    product_name VARCHAR(128),
    spec VARCHAR(255),
    price DECIMAL(10,2),
    qty INT,
    subtotal DECIMAL(10,2),
    coupon_applied TINYINT DEFAULT 0,
    CONSTRAINT fk_detail_order FOREIGN KEY (order_id) REFERENCES sales_order(order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='订单明细';

-- ========== payment_record ==========
CREATE TABLE IF NOT EXISTS payment_record (
    pay_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id VARCHAR(32) NOT NULL,
    amount DECIMAL(10,2),
    channel VARCHAR(32),
    status ENUM('success','pending','failed') DEFAULT 'success',
    pay_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pay_order FOREIGN KEY (order_id) REFERENCES sales_order(order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='支付记录';

-- ========== revenue_daily ==========
CREATE TABLE IF NOT EXISTS revenue_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    store_id BIGINT,
    session_id BIGINT NULL,
    date DATE NOT NULL,
    revenue DECIMAL(12,2) DEFAULT 0,
    orders INT DEFAULT 0,
    avg_ticket DECIMAL(10,2) DEFAULT 0,
    conversion_rate DECIMAL(5,4) DEFAULT 0,
    UNIQUE KEY uk_date_store_session (date, store_id, session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日营收统计';

-- ========== kb_doc ==========
CREATE TABLE IF NOT EXISTS kb_doc (
    doc_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(32) NOT NULL COMMENT '商品知识/话术库/政策/历史FAQ',
    chunk_text TEXT NOT NULL,
    source VARCHAR(255),
    milvus_id VARCHAR(64) NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库';

-- ========== platform_account 外部平台授权账号 ==========
CREATE TABLE IF NOT EXISTS platform_account (
    account_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(16) NOT NULL COMMENT 'DOUYIN/KUAISHOU/WECHAT_CHANNEL',
    account_name VARCHAR(64) NOT NULL,
    shop_id VARCHAR(64) NULL,
    app_key VARCHAR(64) NULL,
    app_secret VARCHAR(255) NULL,
    access_token VARCHAR(500) NULL,
    refresh_token VARCHAR(500) NULL,
    token_expire DATETIME NULL,
    bind_mode VARCHAR(8) DEFAULT 'MOCK' COMMENT 'REAL/MOCK',
    status VARCHAR(16) DEFAULT 'CONNECTED',
    last_sync_at DATETIME NULL,
    store_id BIGINT NULL COMMENT '映射到本地门店',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    KEY idx_pa_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部直播平台授权账号';

-- ========== platform_sync_log 外部平台同步日志 ==========
CREATE TABLE IF NOT EXISTS platform_sync_log (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id BIGINT NOT NULL,
    sync_type VARCHAR(16) NOT NULL COMMENT 'ORDER/PRODUCT/SESSION',
    bind_mode VARCHAR(8) DEFAULT 'MOCK',
    status VARCHAR(16) DEFAULT 'SUCCESS',
    fetched INT DEFAULT 0,
    created_count INT DEFAULT 0,
    updated_count INT DEFAULT 0,
    message VARCHAR(500) NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME NULL,
    KEY idx_synclog_account_time (account_id, started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外部平台同步日志';

SET FOREIGN_KEY_CHECKS = 1;
