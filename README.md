# Project Setup Guide

## Backend (`be/`)

### File Structure
1. **`db.py`** — Handles database connection and configuration.
2. **`models.py`** — Defines ORM models representing database tables.
3. **`controller.py`** — Service entry point.
4. **`controllers/`** — Contains API routes and CRUD (Create, Read, Update, Delete) logic for the app.
5. **`utils/`** — Contains common helper functions used in the whole backend



## Frontend (`fe/`)

### File Structure
1. **`app.py`** — Streamlit entry point for the frontend interface.

---


## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo_url>
cd <repo_name>
```

### 2. Create a Virtual Environment 
```bash
python -m venv hamm_env
```

### 3. Activate the Virtual Environment 
- Windows: 
  ```bash
  hamm_env\Scripts\activate
  ```
- Mac/Linux:
  ```bash
  source hamm_env/bin/activate
  ```

### 4. Install Dependencies 
```bash
pip install -r requirements.txt
```

### 5. Database Preparation 
- PostgreSQL is recommended but other RDBMS should work 
- Open `be/db_prep.sql` and copy all SQL commands 
- Execute them in your DB Client (pgAdmin, SQL Workbench, etc.), they will create tables, triggers, and seed data 

### 6. Configure DB URL 
In the .env file, add your DB connection string: 
```
DATABASE_URL=postgresql+psycopg2://<username>:<password>@localhost:5432/<dbname>
``` 
- username: your database username but defaults to `postgres `
- password: your database password
- DB Name: your database name 

### 7. Running the App 
From the `be/ ` directory: 
```bash 
python controller.py
```
This will start the backend, usually accessible at: 
```cpp
http://127.0.0.1:5000
```

### 8. Testing API Endpoints 
Try visiting (or use Postman):
- ```http://127.0.0.1:5000/transactions```
- ```http://127.0.0.1:5000/users```

You can find more endpoints defined in the urunder the ```@app.route()``` in ```be/controllers.py```. Currently only GET requests are made. 
Current available endpoints are: 
1. **`/transactions`**  : GET, POST
2. **`/users`**         : GET, POST
3. **`/categories`**    : GET, POST
4. **`/budgets`**       : GET, POST

### 9. Running the Frontend
In a new terminal, navigate to ```fe/```
```bash
streamlit run app.py
```
This will start the Streamlit Frontend, which connects to the backend and displays data interactively. 