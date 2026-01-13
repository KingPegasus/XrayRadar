"""
Framework integrations for xrayradar
"""

__all__ = []

try:
    from .flask import FlaskIntegration
    __all__.append("FlaskIntegration")
except ImportError:  # pragma: no cover
    FlaskIntegration = None  # pragma: no cover

try:
    from .django import DjangoIntegration
    __all__.append("DjangoIntegration")
except ImportError:  # pragma: no cover
    DjangoIntegration = None  # pragma: no cover

try:
    from .fastapi import FastAPIIntegration
    __all__.append("FastAPIIntegration")
except ImportError:  # pragma: no cover
    FastAPIIntegration = None  # pragma: no cover

try:
    from .graphene import GrapheneIntegration
    __all__.append("GrapheneIntegration")
except ImportError:  # pragma: no cover
    GrapheneIntegration = None  # pragma: no cover

try:
    from .drf import make_drf_exception_handler
    __all__.append("make_drf_exception_handler")
except ImportError:  # pragma: no cover
    make_drf_exception_handler = None  # pragma: no cover
