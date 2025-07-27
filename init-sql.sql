-- RAG 系統資料庫初始化腳本

-- 創建示例資料表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    category VARCHAR(100),
    stock INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date DATE DEFAULT CURRENT_DATE,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- 創建索引以提升查詢性能
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- 插入示例資料
INSERT INTO products (name, description, price, category, stock) VALUES
    ('筆記型電腦', '高效能商務筆電，適合辦公使用', 35000.00, '電子產品', 50),
    ('無線滑鼠', '人體工學設計，2.4G無線連接', 890.00, '電腦週邊', 200),
    ('機械鍵盤', 'Cherry軸機械鍵盤，RGB背光', 3500.00, '電腦週邊', 100),
    ('顯示器', '27吋 4K IPS顯示器', 12000.00, '電子產品', 30),
    ('辦公椅', '人體工學辦公椅，可調節高度', 8500.00, '辦公家具', 20);

INSERT INTO customers (name, email, phone, address) VALUES
    ('張三', 'zhangsan@example.com', '0912345678', '台北市信義區信義路100號'),
    ('李四', 'lisi@example.com', '0923456789', '新北市板橋區文化路200號'),
    ('王五', 'wangwu@example.com', '0934567890', '台中市西屯區台灣大道300號');

INSERT INTO orders (customer_id, total_amount, status) VALUES
    (1, 38500.00, 'completed'),
    (2, 16390.00, 'processing'),
    (3, 47000.00, 'completed');

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 35000.00),
    (1, 3, 1, 3500.00),
    (2, 2, 2, 890.00),
    (2, 3, 1, 3500.00),
    (2, 4, 1, 12000.00),
    (3, 1, 1, 35000.00),
    (3, 4, 1, 12000.00);

-- 創建查詢範例視圖
CREATE OR REPLACE VIEW sales_summary AS
SELECT 
    DATE_TRUNC('month', o.order_date) as month,
    COUNT(DISTINCT o.id) as order_count,
    COUNT(DISTINCT o.customer_id) as customer_count,
    SUM(o.total_amount) as total_sales,
    AVG(o.total_amount) as avg_order_value
FROM orders o
WHERE o.status = 'completed'
GROUP BY DATE_TRUNC('month', o.order_date);

CREATE OR REPLACE VIEW product_sales AS
SELECT 
    p.name as product_name,
    p.category,
    COUNT(oi.id) as times_sold,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.subtotal) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category;

-- 授予適當的權限
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO raguser;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO raguser;