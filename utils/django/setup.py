import os
import django


def django_setup(environment: str = None):
    # Initialize Django project (only once)
    if hasattr(django_setup, "has_been_called"): return

    # this should be called first
    if environment:
        os.environ['ENVIRONMENT'] = environment

    from config.settings import DJANGO_SETTINGS_MODULE
    os.environ['DJANGO_SETTINGS_MODULE'] = DJANGO_SETTINGS_MODULE

    django.setup()
    django_setup.has_been_called = True


def django_setup_decorator(environment: str = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            django_setup(environment=environment)
            return func(*args, **kwargs)
        return wrapper
    return decorator
