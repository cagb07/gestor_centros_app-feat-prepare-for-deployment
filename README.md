# Gestor de Centros Educativos

This is a Streamlit application for managing educational centers. It provides a user-friendly interface for administrators and operators to manage and view data related to educational centers in Costa Rica.

## Features

- User authentication with roles (admin, operator).
- Admins can manage users, areas, and form templates.
- Operators can fill out forms and view their submissions.
- Data is stored in a PostgreSQL database.
- The application reads initial data from a CSV file.

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a Python virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   - Create a `.streamlit/secrets.toml` file with your PostgreSQL connection string:
     ```toml
     DB_URL = "postgresql://user:password@host:port/database"
     ```
   - Run the database initialization script:
     ```bash
     python init_db.py
     ```

## Running the Application

Once the setup is complete, you can run the Streamlit application:

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`.
