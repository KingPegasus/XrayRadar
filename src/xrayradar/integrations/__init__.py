"""
Framework integrations for xrayradar
"""

__all__ = []

try:
    from .flask import FlaskIntegration
    __all__.append("FlaskIntegration")
except ImportError:
    FlaskIntegration = None

try:
    from .django import DjangoIntegration
    __all__.append("DjangoIntegration")
except ImportError:
    DjangoIntegration = None

try:
    from .fastapi import FastAPIIntegration
    __all__.append("FastAPIIntegration")
except ImportError:
    FastAPIIntegration = None

try:
    from .graphene import GrapheneIntegration
    __all__.append("GrapheneIntegration")
except ImportError:
    GrapheneIntegration = None

try:
    from .drf import make_drf_exception_handler
    __all__.append("make_drf_exception_handler")
except ImportError:
    make_drf_exception_handler = None
