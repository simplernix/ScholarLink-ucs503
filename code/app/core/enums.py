"""
Enum types shared across models. Stored as native Postgres ENUMs (via
SQLAlchemy Enum) rather than free-text strings, per project conventions.
"""
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    PROFESSOR = "professor"
    ADMIN = "admin"


class PaperStatus(str, enum.Enum):
    PROCESSING = "processing"
    PUBLISHED = "published"


class CollaborationRequestStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class NotificationEventType(str, enum.Enum):
    REQUEST_SENT = "request_sent"
    REQUEST_ACCEPTED = "request_accepted"
    REQUEST_DECLINED = "request_declined"
    PAPER_PROCESSING_COMPLETE = "paper_processing_complete"
