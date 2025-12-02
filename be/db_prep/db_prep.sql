
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

-- JOHNS ACTIVITIES
INSERT INTO categories (user_id, name, type)
VALUES
(7, 'Rent', 'expense'),
(7, 'Utilities', 'expense'),
(7, 'Entertainment', 'expense');

-- --- JULY 2025 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(7, 11, 3050.00, 'income', 'Monthly Salary Deposit (Base pay)', '2025-07-01'),
(7, 17, 1500.00, 'expense', 'Monthly Apartment Rent', '2025-07-03'),
(7, 12, 105.00, 'expense', 'High Summer Electricity Bill (A/C)', '2025-07-07'),
(7, 13, 165.50, 'expense', 'Weekly Grocery Shopping', '2025-07-10'),
(7, 18, 90.00, 'expense', 'Weekend Festival Ticket', '2025-07-15'),
(7, 13, 85.00, 'expense', 'Barbecue supplies for gathering', '2025-07-22'),
(7, 19, 65.00, 'expense', 'Monthly Metro Pass', '2025-07-28');


-- --- AUGUST 2025 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(7, 11, 3100.00, 'income', 'Monthly Salary Deposit', '2025-08-01'),
(7, 17, 1500.00, 'expense', 'Monthly Apartment Rent', '2025-08-03'),
(7, 12, 95.50, 'expense', 'Electricity and Water Bill', '2025-08-07'),
(7, 13, 180.25, 'expense', 'Weekly Grocery Shopping', '2025-08-10'),
(7, 18, 45.00, 'expense', 'Concert ticket purchase', '2025-08-15'),
(7, 13, 75.00, 'expense', 'Dining out with friends', '2025-08-22'),
(7, 11, 250.00, 'income', 'Freelance Side Gig Payment', '2025-08-28'),
(7, 19, 20.00, 'expense', 'Uber to airport', '2025-08-30');


-- --- SEPTEMBER 2025 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(7, 11, 3100.00, 'income', 'Monthly Salary Deposit', '2025-09-01'),
(7, 17, 1500.00, 'expense', 'Monthly Apartment Rent', '2025-09-03'),
(7, 12, 110.75, 'expense', 'Internet and Phone Bill', '2025-09-06'),
(7, 13, 195.50, 'expense', 'Weekly Grocery Shopping (Higher amount)', '2025-09-11'),
(7, 13, 45.00, 'expense', 'Dinner delivery', '2025-09-18'),
(7, 18, 75.00, 'expense', 'Weekend trip entrance fee', '2025-09-25'),
(7, 19, 70.00, 'expense', 'Monthly Metro Pass Renewal', '2025-09-27');


-- --- OCTOBER 2025 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(7, 11, 3150.00, 'income', 'Monthly Salary Deposit (Small raise)', '2025-10-01'),
(7, 17, 1500.00, 'expense', 'Monthly Apartment Rent', '2025-10-03'),
(7, 12, 88.20, 'expense', 'Electricity and Water Bill', '2025-10-07'),
(7, 13, 175.00, 'expense', 'Weekly Grocery Shopping', '2025-10-12'),
(7, 13, 110.00, 'expense', 'Dinner party ingredients', '2025-10-20'),
(7, 18, 15.00, 'expense', 'Movie rental', '2025-10-25'),
(7, 11, 150.00, 'income', 'Small Consulting Fee', '2025-10-30'),
(7, 19, 15.00, 'expense', 'Gas for car', '2025-10-31');