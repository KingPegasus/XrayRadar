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
