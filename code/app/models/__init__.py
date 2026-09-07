"""
Import every model module here so that `Base.metadata` is fully populated
before Alembic's `env.py` (or anything else) inspects it for autogeneration.
"""
from app.models.collaboration import CollaborationRequest  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.paper import Paper, PaperAuthor  # noqa: F401
from app.models.topic import PaperInsight, PaperTopic, Topic  # noqa: F401
from app.models.user import User  # noqa: F401
