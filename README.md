# HygGeo

A Django project for geographic data management.

## Installation

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd HygGeo
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Creating Django Models

1. Open your Django app directory (e.g., `HygGeo/`).
2. Edit `models.py` to define your models.
3. Make migrations:
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

## Starting the Development Server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to view your project.
