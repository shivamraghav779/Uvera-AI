"""Imports every ORM model so ``Base.metadata`` is complete (used by Alembic)."""

from app.domains.actions.models import UIAction
from app.domains.assets.models import StoredAsset
from app.domains.conversation.models import ConversationMessage
from app.domains.data_sources.models import DataSource
from app.domains.generation.models import GenerationJob
from app.domains.generative_ui.models import UIVersion
from app.domains.records.models import WorkspaceRecord
from app.domains.references.models import ReferenceComponent
from app.domains.users.models import User
from app.domains.workspaces.models import Workspace

__all__ = [
    "ConversationMessage",
    "DataSource",
    "GenerationJob",
    "ReferenceComponent",
    "StoredAsset",
    "UIAction",
    "UIVersion",
    "User",
    "Workspace",
    "WorkspaceRecord",
]
