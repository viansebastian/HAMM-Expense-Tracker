
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50) DEFAULT 'user'
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('income', 'expense')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('income', 'expense')),
    description TEXT,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    budget_amount NUMERIC(12,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_modtime BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_categories_modtime BEFORE UPDATE ON categories
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_transactions_modtime BEFORE UPDATE ON transactions
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_budgets_modtime BEFORE UPDATE ON budgets
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ========== USERS ==========
INSERT INTO users (email, password_hash, first_name, last_name, role)
VALUES
('admin@app.com', 'admin_hash', 'System', 'Admin', 'admin'),
('sarah@example.com', 'hashed_pw_1', 'Sarah', 'Lee', 'user'),
('john@example.com', 'hashed_pw_2', 'John', 'Doe', 'user');

-- ========== CATEGORIES ==========
INSERT INTO categories (user_id, name, type)
VALUES
-- CHANGE THE user_id to the ID's in ur postgre
-- User 101: Sarah's Categories
(6, 'Paycheck', 'income'),
(6, 'Bonus', 'income'),
(6, 'Groceries', 'expense'),
-- User 102: John's Categories
(7, 'Paycheck', 'income'),
(7, 'Utilities', 'expense'),
(7, 'Food', 'expense');

-- ========== TRANSACTIONS ==========
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
-- CHANGE THE USER_ID and CATEGORY_ID to the ID's in ur postgre
-- --- NOVEMBER 2024 ---
(6, 8, 2550.00, 'income', 'Monthly Paycheck Deposit', '2024-11-01'),
(6, 9, 510.00, 'income', 'Performance Bonus', '2024-11-15'),
(6, 10, 345.00, 'expense', 'Monthly grocery expense sum', '2024-11-20'),
(7, 11, 2980.00, 'income', 'Monthly Paycheck Deposit', '2024-11-01'),
(7, 12, 125.00, 'expense', 'Monthly Utility Payment (Water/Gas/Elec)', '2024-11-10'),
(7, 13, 260.00, 'expense', 'Sum of dining and food expenses', '2024-11-25'),

-- --- DECEMBER 2024 ---
(6, 8, 2480.00, 'income', 'Monthly Paycheck Deposit (Slightly less)', '2024-12-01'),
(6, 9, 490.00, 'income', 'Holiday Bonus', '2024-12-15'),
(6, 10, 360.00, 'expense', 'Monthly grocery expense sum (Higher due to holidays)', '2024-12-20'),
(7, 11, 3020.00, 'income', 'Monthly Paycheck Deposit (Slightly more)', '2024-12-01'),
(7, 12, 115.00, 'expense', 'Monthly Utility Payment (Lower usage)', '2024-12-10'),
(7, 13, 240.00, 'expense', 'Sum of dining and food expenses', '2024-12-25'),

-- --- JANUARY 2025 ---
(6, 8, 2520.00, 'income', 'Monthly Paycheck Deposit', '2025-01-01'),
(6, 9, 520.00, 'income', 'Small Project Bonus', '2025-01-15'),
(6, 10, 330.00, 'expense', 'Monthly grocery expense sum (Post-holiday dip)', '2025-01-20'),
(7, 11, 2950.00, 'income', 'Monthly Paycheck Deposit (Project delay)', '2025-01-01'),
(7, 12, 130.00, 'expense', 'Monthly Utility Payment (Heating costs)', '2025-01-10'),
(7, 13, 270.00, 'expense', 'Sum of dining and food expenses', '2025-01-25'),

-- --- FEBRUARY 2025 ---
(6, 8, 2490.00, 'income', 'Monthly Paycheck Deposit', '2025-02-01'),
(6, 9, 505.00, 'income', 'Small Bonus', '2025-02-15'),
(6, 10, 375.00, 'expense', 'Monthly grocery expense sum (highest fluctuation)', '2025-02-20'),
(7, 11, 3050.00, 'income', 'Monthly Paycheck Deposit (Extra shift)', '2025-02-01'),
(7, 12, 110.00, 'expense', 'Monthly Utility Payment', '2025-02-10'),
(7, 13, 230.00, 'expense', 'Sum of dining and food expenses (Low)', '2025-02-25'),

-- --- MARCH 2025 ---
(6, 8, 2510.00, 'income', 'Monthly Paycheck Deposit', '2025-03-01'),
(6, 9, 480.00, 'income', 'End of Quarter Bonus (Lower)', '2025-03-15'),
(6, 10, 350.00, 'expense', 'Monthly grocery expense sum (Back to average)', '2025-03-20'),
(7, 11, 2990.00, 'income', 'Monthly Paycheck Deposit', '2025-03-01'),
(7, 12, 122.00, 'expense', 'Monthly Utility Payment', '2025-03-10'),
(7, 13, 250.00, 'expense', 'Sum of dining and food expenses', '2025-03-25');

-- ========== BUDGETS ==========
INSERT INTO budgets (user_id, category_id, budget_amount, start_date, end_date)
VALUES
-- CHANGE THE USER_ID and CATEGORY_ID to the ID's in ur postgre
-- User 101: Groceries Budget $350/month for 5 months
(6, 10, 350.00, '2024-11-01', '2024-11-30'),
(6, 10, 350.00, '2024-12-01', '2024-12-31'),
(6, 10, 350.00, '2025-01-01', '2025-01-31'),
(6, 10, 350.00, '2025-02-01', '2025-02-28'),
(6, 10, 350.00, '2025-03-01', '2025-03-31');