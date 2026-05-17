"""
__init__.py — forces Django to initialise Celery when the project starts.

Importing celery_app here guarantees the Celery application instance is
created as soon as Django's app registry is ready.  Without this import,
the Celery app would only be created when the `celery` CLI runs — meaning
the Django web process itself would never register tasks, and task
autodiscovery would be silently incomplete.

The __all__ declaration makes celery_app an explicit public export of the
package, satisfying Django's autodiscovery conventions.
"""

from .celery import app as celery_app

__all__ = ("celery_app",)
