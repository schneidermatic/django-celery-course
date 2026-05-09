"""
__init__.py — forces Django to initialise Celery when the project starts.

Importing celery_app here ensures the Celery application instance is created
as soon as Django's app registry is ready.  Without this import the Celery
application would only be created when the `celery` CLI is executed, meaning
the Django web process itself would have no knowledge of Celery configuration
and shared-task discovery would be delayed or incomplete.

The `__all__` declaration makes celery_app an explicit public export of the
package and satisfies Django's autodiscovery conventions.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
