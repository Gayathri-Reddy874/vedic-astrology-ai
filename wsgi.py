"""WSGI entry point: ``gunicorn wsgi:app``."""

from vedic_astro import create_app

app = create_app()

