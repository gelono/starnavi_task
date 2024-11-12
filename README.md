# starnavi_task

This project is an implementation of a backend API that allows you to create posts and comments, 
which in turn are checked by an AI service for inappropriate content.

The AI ​​model used is 'gemini-1.5-flash'. The model was tested using English-language content.

# Django Project

## Description
This is a Django project utilizing PostgreSQL as the database and Django Ninja for API development.

## Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- Virtual Environment (recommended)

### Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/gelono/starnavi_task.git
   cd starnavi_task
   
2. Create and activate a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # For Linux/Mac
    venv\Scripts\activate     # For Windows

3. Install dependencies:
    ```bash
   pip install -r requirements.txt
   
4. Configure the PostgreSQL database:
    ```bash
   CREATE DATABASE your_db_name;
    CREATE USER your_db_user WITH PASSWORD 'your_db_password';
    ALTER ROLE your_db_user SET client_encoding TO 'utf8';
    ALTER ROLE your_db_user SET default_transaction_isolation TO 'read committed';
    ALTER ROLE your_db_user SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;

5. Update settings.py with your PostgreSQL database configuration:
    ```bash
   DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

6. Apply migrations:
   ```bash
   python manage.py migrate
   
7. Run the development server:
    ```bash
   python manage.py runserver

Running Tests
1. To run tests, use the following command:
    ```bash
    pytest -v

API Documentation
Django Ninja automatically generates interactive API documentation. 
Visit http://localhost:8000/api/docs to access the documentation.