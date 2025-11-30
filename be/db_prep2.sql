INSERT INTO categories (user_id, name, type)
VALUES
(102, 'Rent', 'expense'),
(102, 'Utilities', 'expense'),
(102, 'Entertainment', 'expense');

-- --- JULY 2023 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(102, 209, 3050.00, 'income', 'Monthly Salary Deposit (Base pay)', '2023-07-01'),
(102, 1, 1500.00, 'expense', 'Monthly Apartment Rent', '2023-07-03'),
(102, 2, 105.00, 'expense', 'High Summer Electricity Bill (A/C)', '2023-07-07'),
(102, 207, 165.50, 'expense', 'Weekly Grocery Shopping', '2023-07-10'),
(102, 3, 90.00, 'expense', 'Weekend Festival Ticket', '2023-07-15'),
(102, 207, 85.00, 'expense', 'Barbecue supplies for gathering', '2023-07-22'),
(102, 208, 65.00, 'expense', 'Monthly Metro Pass', '2023-07-28');


-- --- AUGUST 2023 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(102, 209, 3100.00, 'income', 'Monthly Salary Deposit', '2023-08-01'),
(102, 1, 1500.00, 'expense', 'Monthly Apartment Rent', '2023-08-03'),
(102, 2, 95.50, 'expense', 'Electricity and Water Bill', '2023-08-07'),
(102, 207, 180.25, 'expense', 'Weekly Grocery Shopping', '2023-08-10'),
(102, 3, 45.00, 'expense', 'Concert ticket purchase', '2023-08-15'),
(102, 207, 75.00, 'expense', 'Dining out with friends', '2023-08-22'),
(102, 209, 250.00, 'income', 'Freelance Side Gig Payment', '2023-08-28'),
(102, 208, 20.00, 'expense', 'Uber to airport', '2023-08-30');


-- --- SEPTEMBER 2023 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(102, 209, 3100.00, 'income', 'Monthly Salary Deposit', '2023-09-01'),
(102, 1, 1500.00, 'expense', 'Monthly Apartment Rent', '2023-09-03'),
(102, 2, 110.75, 'expense', 'Internet and Phone Bill', '2023-09-06'),
(102, 207, 195.50, 'expense', 'Weekly Grocery Shopping (Higher amount)', '2023-09-11'),
(102, 207, 45.00, 'expense', 'Dinner delivery', '2023-09-18'),
(102, 3, 75.00, 'expense', 'Weekend trip entrance fee', '2023-09-25'),
(102, 208, 70.00, 'expense', 'Monthly Metro Pass Renewal', '2023-09-27');


-- --- OCTOBER 2023 ---
INSERT INTO transactions (user_id, category_id, amount, type, description, transaction_date)
VALUES
(102, 209, 3150.00, 'income', 'Monthly Salary Deposit (Small raise)', '2023-10-01'),
(102, 1, 1500.00, 'expense', 'Monthly Apartment Rent', '2023-10-03'),
(102, 2, 88.20, 'expense', 'Electricity and Water Bill', '2023-10-07'),
(102, 207, 175.00, 'expense', 'Weekly Grocery Shopping', '2023-10-12'),
(102, 207, 110.00, 'expense', 'Dinner party ingredients', '2023-10-20'),
(102, 3, 15.00, 'expense', 'Movie rental', '2023-10-25'),
(102, 209, 150.00, 'income', 'Small Consulting Fee', '2023-10-30'),
(102, 208, 15.00, 'expense', 'Gas for car', '2023-10-31');