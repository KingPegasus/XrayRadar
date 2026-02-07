"""Tests for email logging utility."""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

from xrayradar_server.email_log import log_email
from xrayradar_server.models import EmailLog


def test_log_email_success(database_url, monkeypatch):
    """Test successful email logging."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    dbmod.init_db()
    
    db = dbmod.SessionLocal()
    try:
        # Clean up
        db.query(models.EmailLog).delete()
        db.commit()
        
        # Log a successful email
        log_email(
            db=db,
            email_type="verification",
            recipient_email="test@example.com",
            success=True,
            user_id=1,
        )
        
        # Verify it was logged
        logs = db.query(models.EmailLog).all()
        assert len(logs) == 1
        assert logs[0].email_type == "verification"
        assert logs[0].recipient_email == "test@example.com"
        assert logs[0].success is True
        assert logs[0].user_id == 1
        assert logs[0].project_id is None
        assert logs[0].error_message is None
    finally:
        db.close()


def test_log_email_with_error_message(database_url, monkeypatch):
    """Test email logging with error message (truncation)."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    
    import xrayradar_server.db as dbmod
    import xrayradar_server.models as models
    dbmod.init_db()
    
    db = dbmod.SessionLocal()
    try:
        # Clean up
        db.query(models.EmailLog).delete()
        db.commit()
        
        # Log a failed email with long error message
        long_error = "x" * 2000
        log_email(
            db=db,
            email_type="error_alert",
            recipient_email="alert@example.com",
            success=False,
            project_id=1,
            error_message=long_error,
        )
        
        # Verify it was logged with truncated error message
        logs = db.query(models.EmailLog).all()
        assert len(logs) == 1
        assert logs[0].email_type == "error_alert"
        assert logs[0].recipient_email == "alert@example.com"
        assert logs[0].success is False
        assert logs[0].project_id == 1
        assert len(logs[0].error_message) == 1000
        assert logs[0].error_message == "x" * 1000
    finally:
        db.close()


def test_log_email_handles_db_error(database_url, monkeypatch):
    """Test that log_email handles database errors gracefully."""
    monkeypatch.setenv("XRAYRADAR_DATABASE_URL", database_url)
    
    import xrayradar_server.db as dbmod
    dbmod.init_db()
    
    db = dbmod.SessionLocal()
    try:
        # Create a mock db that raises on commit
        mock_db = MagicMock(spec=Session)
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock(side_effect=Exception("DB error"))
        mock_db.rollback = MagicMock()
        
        # Should not raise, should call rollback
        log_email(
            db=mock_db,
            email_type="verification",
            recipient_email="test@example.com",
            success=True,
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_called_once()
    finally:
        db.close()
