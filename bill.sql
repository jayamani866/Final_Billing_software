-- ===============================
-- DATABASE
-- ===============================
CREATE DATABASE IF NOT EXISTS billing_db;
USE billing_db;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS barcode_print_log;
DROP TABLE IF EXISTS sales_items;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS bill_items;
DROP TABLE IF EXISTS billing_items;
DROP TABLE IF EXISTS billing;
DROP TABLE IF EXISTS stock_log;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS offers;
DROP TABLE IF EXISTS shops;

SET FOREIGN_KEY_CHECKS = 1;

-- ===============================
-- SHOPS
-- ===============================
USE billing_db;
CREATE TABLE shops (
    shop_id INT AUTO_INCREMENT PRIMARY KEY,
    owner_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO shops (owner_name, username, password)
VALUES ('Krish', 'yuva', '123');

-- ===============================
-- PRODUCTS
-- ===============================
CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,

    product_name VARCHAR(255) NOT NULL,
    product_print_name VARCHAR(255),

    barcode1 VARCHAR(255),
    barcode2 VARCHAR(255),
    barcode3 VARCHAR(255),

    mrp_rate DOUBLE DEFAULT 0,
    purchase_rate DOUBLE DEFAULT 0,
    selling_price DOUBLE DEFAULT 0,
   
    sale_wholesale DOUBLE DEFAULT 0,

    stock INT DEFAULT 0,

    gst_sgst DOUBLE DEFAULT 0,
    gst_cgst DOUBLE DEFAULT 0,

    hsn VARCHAR(50),
    hsn_code VARCHAR(50),

    category VARCHAR(255),

    type ENUM('Company','Other') DEFAULT 'Company',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
) ENGINE=InnoDB;



SELECT product_id, product_name, barcode1
FROM products;

SELECT 
    p.product_name,
    c.category_name
FROM products p
LEFT JOIN categories c
ON p.category_id = c.category_id;


ALTER TABLE products
ADD COLUMN category_id INT AFTER hsn_code;

ALTER TABLE products
DROP COLUMN category;

ALTER TABLE products
ADD CONSTRAINT fk_products_category
FOREIGN KEY (category_id)
REFERENCES categories(category_id);

UPDATE products
SET category_id = (
    SELECT category_id FROM categories WHERE category_name='General'
)
WHERE category_id IS NULL;

-- ===============================
-- STOCK
-- ===============================
CREATE TABLE stock (
    stock_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    qty INT DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

-- ===============================
-- STOCK LOG
-- ===============================
CREATE TABLE stock_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    change_type VARCHAR(100),
    quantity INT,
    note VARCHAR(255),
    date_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

-- ===============================
-- CUSTOMERS
-- ===============================
CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,

    shop_id INT NOT NULL,

    customer_name VARCHAR(255) NOT NULL,

    phone_1 VARCHAR(20) NOT NULL,
    phone_2 VARCHAR(20) DEFAULT NULL,

    address TEXT DEFAULT NULL,
    email VARCHAR(255) DEFAULT NULL,

    last_purchase_datetime DATETIME NULL,
    last_purchase_amount DOUBLE DEFAULT 0,

    lifetime_total DOUBLE DEFAULT 0,

    total_points INT DEFAULT 0,
    current_points INT DEFAULT 0,
    spent_points INT DEFAULT 0,

    status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE (shop_id, phone_1),

    FOREIGN KEY (shop_id)
        REFERENCES shops(shop_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

DESCRIBE customers;

SHOW INDEX FROM customers;

SELECT * FROM customers;




-- ===============================
-- BILLING (HEADER)
-- ===============================
CREATE TABLE billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,
    bill_no VARCHAR(255),
    customer_phone VARCHAR(255),
    customer_name VARCHAR(255),
    total_amount DOUBLE DEFAULT 0,
    bill_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
) ENGINE=InnoDB;

-- ===============================
-- BILLING ITEMS
-- ===============================
CREATE TABLE billing_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    product_name VARCHAR(255),
    mrp DOUBLE DEFAULT 0,
    price DOUBLE DEFAULT 0,
    qty INT DEFAULT 1,
    amount DOUBLE DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES billing(bill_id)
) ENGINE=InnoDB;

ALTER TABLE billing_items
ADD COLUMN product_id INT AFTER bill_id,
ADD COLUMN barcode VARCHAR(255) AFTER product_id,

ADD COLUMN purchase_rate DOUBLE DEFAULT 0 AFTER mrp,
ADD COLUMN sale_rate DOUBLE DEFAULT 0 AFTER purchase_rate,

ADD COLUMN stock INT DEFAULT 0 AFTER qty,

ADD COLUMN discount_percent DOUBLE DEFAULT 0 AFTER stock,
ADD COLUMN gst_percent DOUBLE DEFAULT 0 AFTER discount_percent,

ADD COLUMN profit DOUBLE DEFAULT 0 AFTER amount,
ADD COLUMN loss DOUBLE DEFAULT 0 AFTER profit;

ALTER TABLE billing_items
ADD CONSTRAINT fk_billing_items_product
FOREIGN KEY (product_id)
REFERENCES products(product_id);


ALTER TABLE billing_items
DROP COLUMN price;

ALTER TABLE billing_items
ADD COLUMN price DOUBLE DEFAULT 0 AFTER purchase_rate;

ALTER TABLE billing_items
DROP COLUMN sale_rate;


ALTER TABLE billing_items
DROP FOREIGN KEY billing_items_ibfk_1;

ALTER TABLE billing_items
ADD CONSTRAINT fk_billing_items_sales
FOREIGN KEY (bill_id)
REFERENCES sales(sale_id)
ON DELETE CASCADE;

SHOW CREATE TABLE billing_items;


SELECT
    p.barcode1,
    p.product_name,
    p.mrp_rate,
    p.purchase_rate,
    si.price,
    si.quantity,
    p.stock,
    0 AS discount_percent,
    (p.gst_sgst + p.gst_cgst) AS gst_percent,
    si.subtotal,

    CASE
        WHEN si.price > p.purchase_rate
        THEN (si.price - p.purchase_rate) * si.quantity
        ELSE 0
    END AS profit,

    CASE
        WHEN si.price < p.purchase_rate
        THEN (p.purchase_rate - si.price) * si.quantity
        ELSE 0
    END AS loss

FROM sales_items si
JOIN products p ON si.product_id = p.product_id
JOIN sales s ON si.sale_id = s.sale_id
ORDER BY si.sale_id DESC;


SELECT
    DATE(s.date_time) AS bill_date,
    TIME(s.date_time) AS bill_time,

    p.barcode1,
    p.product_name,
    p.mrp_rate,
    p.purchase_rate,

    si.price AS sale_price,
    SUM(si.quantity) AS total_qty,
    p.stock,

    0 AS discount_percent,
    (p.gst_sgst + p.gst_cgst) AS gst_percent,

    SUM(si.subtotal) AS total_amount,

    SUM(
        CASE
            WHEN si.price > p.purchase_rate
            THEN (si.price - p.purchase_rate) * si.quantity
            ELSE 0
        END
    ) AS total_profit,

    SUM(
        CASE
            WHEN si.price < p.purchase_rate
            THEN (p.purchase_rate - si.price) * si.quantity
            ELSE 0
        END
    ) AS total_loss

FROM sales_items si
JOIN products p ON si.product_id = p.product_id
JOIN sales s ON si.sale_id = s.sale_id

GROUP BY
    bill_date,
    bill_time,
    p.barcode1,
    p.product_name,
    p.mrp_rate,
    p.purchase_rate,
    si.price,
    p.stock,
    p.gst_sgst,
    p.gst_cgst

ORDER BY
    bill_date DESC,
    bill_time DESC;


DESCRIBE billing_items;


-- ===============================
-- SALES
-- ===============================

CREATE TABLE sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,

    shop_id INT NOT NULL,
    customer_id INT,

    total_amount DOUBLE NOT NULL,
    discount DOUBLE DEFAULT 0,

    payment_method VARCHAR(50),

    given_amount DOUBLE DEFAULT 0,
    return_amount DOUBLE DEFAULT 0,
    points_added INT DEFAULT 0,

    date_time DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (shop_id) REFERENCES shops(shop_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

SHOW CREATE TABLE sales;
SELECT * FROM sales LIMIT 5;
DESCRIBE sales;

-- ===============================
-- SALES ITEMS
-- ===============================
CREATE TABLE sales_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT,
    price DOUBLE,
    subtotal DOUBLE,
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

ALTER TABLE sales_items ADD COLUMN name VARCHAR(255);

DESCRIBE sales_items;

-- ===============================
-- BARCODE PRINT LOG
-- ===============================
CREATE TABLE barcode_print_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    printed_qty INT,
    printed_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
) ENGINE=InnoDB;

-- ===============================
-- STAFF
-- ===============================
CREATE TABLE suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,

    shop_id INT NULL,

    supplier_name VARCHAR(255) NOT NULL,

    phone1 VARCHAR(20),

    phone2 VARCHAR(20),

    supplier_email VARCHAR(255),

    company_name VARCHAR(255),

    address TEXT,

    join_date DATE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS suppliers;

CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT NOT NULL,

    staff_name VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,

    phone1 VARCHAR(20) NOT NULL,
    phone2 VARCHAR(20),

    email VARCHAR(255),
    address TEXT,

    join_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (shop_id) REFERENCES shops(shop_id),

    UNIQUE (shop_id, phone1)
) ENGINE=InnoDB;

DESC staff;


CREATE TABLE admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,

    admin_name VARCHAR(255) NOT NULL,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,

    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ===============================
-- OFFERS
-- ===============================
CREATE TABLE offers (
    offer_id INT AUTO_INCREMENT PRIMARY KEY,
    shop_id INT,
    min_amount DOUBLE,
    discount_percent DOUBLE,
    start_date DATE,
    end_date DATE,
    FOREIGN KEY (shop_id) REFERENCES shops(shop_id)
) ENGINE=InnoDB;



CREATE TABLE shop_details (
    shop_id INT AUTO_INCREMENT PRIMARY KEY,

    shop_name VARCHAR(255) NOT NULL,

    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),

    district VARCHAR(100),
    pincode VARCHAR(10),

    phone1 VARCHAR(20),
    phone2 VARCHAR(20),
    phone3 VARCHAR(20),

    fax VARCHAR(50),
    website VARCHAR(255),

    email1 VARCHAR(255),
    email2 VARCHAR(255),

    gst_number VARCHAR(50),
    shop_code VARCHAR(50) UNIQUE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);




CREATE TABLE expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,

    expense_date DATE NOT NULL,

    category VARCHAR(100) NOT NULL,

    expense_name VARCHAR(255) NOT NULL,

    amount DECIMAL(10,2) NOT NULL,

    payment_mode VARCHAR(50),

    paid_to VARCHAR(255),

    bill_no VARCHAR(100),

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


SELECT expense_date, category, expense_name,
       amount, payment_mode, paid_to,
       expense_id
FROM expenses
ORDER BY expense_date DESC

UPDATE expenses SET notes = NULL WHERE expense_id = 5;


CREATE TABLE income (
    income_id INT AUTO_INCREMENT PRIMARY KEY,

    income_date DATE NOT NULL,

    income_type VARCHAR(50) NOT NULL,
    payment_mode VARCHAR(30) NOT NULL,

    amount DECIMAL(10,2) NOT NULL,

    invoice_no VARCHAR(50),
    customer_name VARCHAR(100),

    gst_applied TINYINT(1) DEFAULT 0,
    gst_amount DECIMAL(10,2) DEFAULT 0,
    net_amount DECIMAL(10,2),

    description TEXT,

    received_by VARCHAR(100),
    reference_no VARCHAR(100),

    status VARCHAR(20) DEFAULT 'Received',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE banks (
    bank_id INT AUTO_INCREMENT PRIMARY KEY,

    bank_name VARCHAR(100) NOT NULL,          -- SBI, HDFC, Cash, GPay
    account_holder VARCHAR(100),              -- Optional (Cash-ku NULL)

    account_no VARCHAR(30),                   -- Bank / Card number
    ifsc_code VARCHAR(15),                    -- Bank IFSC

    bank_type ENUM(
        'Bank',
        'Cash',
        'UPI',
        'Card',
        'Wallet'
    ) NOT NULL DEFAULT 'Bank',

    opening_balance DECIMAL(12,2) DEFAULT 0,
    current_balance DECIMAL(12,2) DEFAULT 0,

    remarks VARCHAR(255),                     -- Notes / Description

    status ENUM('Active','Inactive') DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE tax_master (
    tax_id INT AUTO_INCREMENT PRIMARY KEY,

    tax_name VARCHAR(50) NOT NULL,        -- GST, CGST, SGST, IGST
    tax_code VARCHAR(20),                 -- Optional: GST18, CGST9

    tax_type ENUM(
        'Percentage',
        'Fixed'
    ) NOT NULL DEFAULT 'Percentage',

    tax_rate DECIMAL(6,2) NOT NULL,       -- 18.00, 5.00 etc

    applied_on ENUM(
        'Income',
        'Expense',
        'Both'
    ) NOT NULL DEFAULT 'Income',

    is_compound TINYINT(1) DEFAULT 0,      -- CGST + SGST logic (future use)

    status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active',

    remarks VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,

    company_name VARCHAR(100) NOT NULL,

    purchase_date DATE NOT NULL,

    invoice_no VARCHAR(50) NOT NULL UNIQUE,

    supplier_id INT NOT NULL,

    bill_type ENUM('Cash', 'Credit') NOT NULL DEFAULT 'Cash',

    sub_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    tax_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    discount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    grand_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    paid_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    balance_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    payment_status ENUM('Paid', 'Partial', 'Pending') NOT NULL DEFAULT 'Paid',

    payment_mode ENUM('Cash', 'UPI', 'Bank') NOT NULL DEFAULT 'Cash',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_purchases_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id)
);

ALTER TABLE purchases
MODIFY supplier_id INT NULL;
ALTER TABLE purchases
DROP FOREIGN KEY fk_purchases_supplier;


DESC suppliers;

CREATE TABLE bill_estimates (
    estimate_id INT AUTO_INCREMENT PRIMARY KEY,

    estimate_no VARCHAR(50),
    estimate_date DATETIME DEFAULT CURRENT_TIMESTAMP,

    sno INT,
    product_name VARCHAR(255),

    mrp DECIMAL(10,2),
    price DECIMAL(10,2),
    qty INT,
    amount DECIMAL(10,2),

    total_amount DECIMAL(10,2),
    given_amount DECIMAL(10,2),
    return_amount DECIMAL(10,2)
);

DROP TABLE IF EXISTS bill_estimates;


CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_no VARCHAR(50),
    customer_id INT,
    customer_name VARCHAR(100),
    customer_phone VARCHAR(15),
    transaction_type VARCHAR(10),
    bill_total DECIMAL(10,2),
    amount_given DECIMAL(10,2),
    return_amount DECIMAL(10,2),
    status VARCHAR(10),
    trans_date DATE,
    trans_time TIME
);
