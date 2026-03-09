# Gluko Backend

Django REST API backend for **Gluko** — an AI-powered diabetes assistant that helps users estimate carbohydrates, calculate insulin bolus doses, log health data, and interact with an AI tutor.

## Tech Stack
- Python / Django 5 + Django REST Framework
- PostgreSQL (AWS RDS)
- AWS S3 (food images, audio files)
- JWT Authentication

## Project Structure
```
gluko-backend/
├── data/          # Datasets and raw data files
├── docs/          # Documentation and architecture notes
├── notebooks/     # Jupyter notebooks for exploration and ML
└── ...            # Django app code
```

## Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Team
- Fernando Salinas (@fjsalinasUTS)
- Rohan (@Rohan-UTS)
- Michael
