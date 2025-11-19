
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
INSERT INTO users (id, email, password_hash, first_name, last_name, created_at, updated_at)
VALUES
(101, 'sarah@example.com', 'hashed_pw_1', 'Sarah', 'Lee', '2023-01-15 10:00:00', '2023-10-20 14:30:00', 'user'),
(102, 'john@example.com', 'hashed_pw_2', 'John', 'Doe', '2023-02-01 11:30:00', '2023-11-05 09:15:00', 'user'),
(103, 'maria@example.com', 'hashed_pw_3', 'Maria', 'Garcia', '2023-03-10 15:00:00', '2023-09-22 10:00:00', 'user');

-- ========== CATEGORIES ==========
INSERT INTO categories (id, user_id, name, type, created_at, updated_at)
VALUES
(201, 101, 'Groceries', 'expense', '2023-01-16 09:00:00', '2023-01-16 09:00:00'),
(202, 101, 'Rent', 'expense', '2023-01-16 09:05:00', '2023-01-16 09:05:00'),
(203, 101, 'Salary', 'income', '2023-01-16 09:10:00', '2023-01-16 09:10:00'),
(204, 101, 'Utilities', 'expense', '2023-01-16 09:15:00', '2023-01-16 09:15:00'),
(205, 101, 'Freelance Project', 'income', '2023-01-16 09:20:00', '2023-01-16 09:20:00'),
(206, 101, 'Dining Out', 'expense', '2023-01-16 09:25:00', '2023-01-16 09:25:00'),
(207, 102, 'Food', 'expense', '2023-02-02 10:00:00', '2023-02-02 10:00:00'),
(208, 102, 'Transportation', 'expense', '2023-02-02 10:05:00', '2023-02-02 10:05:00'),
(209, 102, 'Paycheck', 'income', '2023-02-02 10:10:00', '2023-02-02 10:10:00');

-- ========== TRANSACTIONS ==========
INSERT INTO transactions (id, user_id, category_id, amount, type, description, transaction_date, created_at, updated_at)
VALUES
(301, 101, 203, 2500.00, 'income', 'Monthly Salary', '2023-11-01', '2023-11-01 10:00:00', '2023-11-01 10:00:00'),
(302, 101, 202, 1200.00, 'expense', 'Monthly Rent', '2023-11-01', '2023-11-01 10:05:00', '2023-11-01 10:05:00'),
(303, 101, 201, 75.50, 'expense', 'Weekly groceries at SuperMart', '2023-11-03', '2023-11-03 14:10:00', '2023-11-03 14:10:00'),
(304, 101, 206, 45.00, 'expense', 'Dinner with friends', '2023-11-04', '2023-11-04 20:30:00', '2023-11-04 20:30:00'),
(305, 101, 204, 80.00, 'expense', 'Electricity bill', '2023-11-07', '2023-11-07 11:00:00', '2023-11-07 11:00:00'),
(306, 101, 201, 60.25, 'expense', 'Mid-week grocery run', '2023-11-08', '2023-11-08 17:45:00', '2023-11-08 17:45:00'),
(307, 101, 205, 750.00, 'income', 'Client project payment', '2023-11-10', '2023-11-10 09:00:00', '2023-11-10 09:00:00'),
(308, 102, 207, 55.00, 'expense', 'Lunch', '2023-11-02', '2023-11-02 13:00:00', '2023-11-02 13:00:00'),
(309, 102, 209, 3000.00, 'income', 'Monthly Paycheck', '2023-11-05', '2023-11-05 09:00:00', '2023-11-05 09:00:00'),
(310, 101, 206, 20.00, 'expense', 'Coffee and pastry', '2023-11-12', '2023-11-12 11:15:00', '2023-11-12 11:15:00');

-- ========== BUDGETS ==========
INSERT INTO budgets (id, user_id, category_id, budget_amount, start_date, end_date, created_at, updated_at)
VALUES
(401, 101, 201, 300.00, '2023-11-01', '2023-11-30', '2023-10-25 10:00:00', '2023-10-25 10:00:00'),
(402, 101, 206, 150.00, '2023-11-01', '2023-11-30', '2023-10-25 10:05:00', '2023-10-25 10:05:00'),
(403, 101, 204, 100.00, '2023-11-01', '2023-11-30', '2023-10-25 10:10:00', '2023-10-25 10:10:00');
