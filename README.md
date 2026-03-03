# MotorMatch

> **Early stages** — we're just getting started, things will break and change a lot.

MotorMatch is a car matching web app built with Django. The idea is to help people find cars that suit them. Still very much a work in progress.

## Stack

- Python / Django 4.2
- PostgreSQL
- Gunicorn + Heroku for deployment

## Running it locally

You'll need Python 3 and PostgreSQL installed.

```bash
git clone https://github.com/pdblackburn0-del/motormatch.git
cd motormatch

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Then go to `http://127.0.0.1:8000/`.

## Notes

- This is a group project (team of 4) for uni
- Lots of features are missing or placeholder right now
- Don't expect anything to be stable yet
