"""
Central model registry — import every ORM model here so that
``Base.metadata`` contains the full schema when Alembic or the
application starts.

Usage::

    from app.storage.models import Base          # for metadata
    from app.storage.models import User, Project  # individual models
"""

from app.storage.models.audit_log import AuditLog
from app.storage.models.base import Base
from app.storage.models.experiment import Experiment
from app.storage.models.feedback import Feedback
from app.storage.models.firewall_log import FirewallLog
from app.storage.models.firewall_rule import FirewallRule
from app.storage.models.monad_attestation import MonadAttestation
from app.storage.models.project import Project
from app.storage.models.provider import ModelProvider
from app.storage.models.result import Result
from app.storage.models.test_case import TestCase
from app.storage.models.user import User

__all__ = [
    "Base",
    "AuditLog",
    "Experiment",
    "Feedback",
    "FirewallLog",
    "FirewallRule",
    "MonadAttestation",
    "ModelProvider",
    "Project",
    "Result",
    "TestCase",
    "User",
]
