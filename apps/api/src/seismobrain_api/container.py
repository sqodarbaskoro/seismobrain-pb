"""
File: container.py
Description: Application dependency container for FastAPI DI wiring
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-17
Version: 0.2.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from __future__ import annotations

from dataclasses import dataclass, field

from seismobrain_adapters.evidence.inline import InlineEvidenceSnapshotStore
from seismobrain_adapters.llm.transport import HttpxJsonTransport, JsonHttpTransport
from seismobrain_api.admin_catalog import AdminCatalog
from seismobrain_api.analytics import AnalyticsStore
from seismobrain_api.auth.api_tokens import ApiTokenStore, InMemoryApiTokenStore
from seismobrain_api.auth.lockout import AccountLockout
from seismobrain_api.auth.oidc import MockOidcProvider, OidcService, OidcSettings
from seismobrain_api.auth.tokens import InMemoryRefreshTokenStore, RefreshTokenStore
from seismobrain_api.auth.users import UserStore
from seismobrain_api.collection_access import InMemoryCollectionAccessStore
from seismobrain_api.config import Settings
from seismobrain_api.conversations import ConversationStore
from seismobrain_api.custom_metadata import CustomMetadataStore
from seismobrain_api.document_actions import BulkDocumentStore
from seismobrain_api.feedback_store import FeedbackStore
from seismobrain_api.glossary_store import GlossaryStore
from seismobrain_api.groups import GroupStore
from seismobrain_api.quarantine import QuarantineStore
from seismobrain_api.resource_guard import InMemoryDocumentAccessStore
from seismobrain_api.search_index import InMemorySearchIndex
from seismobrain_api.sqlite_admin_catalog import SqliteAdminCatalog
from seismobrain_api.startup_index_guard import ActiveIndexInfo, ConfiguredIndexInfo
from seismobrain_core.object_authz import ObjectOwnershipStore
from seismobrain_core.ports import (
    AuthorizationGuard,
    EventLog,
    EvidenceSnapshotStore,
    JobQueue,
    MetadataStore,
    ObjectStore,
    RateLimiter,
)


@dataclass(slots=True)
class AppContainer:
    """Holds port implementations and config for the API process."""

    settings: Settings
    metadata_store: MetadataStore
    job_queue: JobQueue
    object_store: ObjectStore
    event_log: EventLog
    rate_limiter: RateLimiter
    authorization_guard: AuthorizationGuard
    user_store: UserStore
    llm_transport: JsonHttpTransport = field(default_factory=HttpxJsonTransport)
    refresh_token_store: RefreshTokenStore = field(
        default_factory=InMemoryRefreshTokenStore
    )
    account_lockout: AccountLockout = field(default_factory=AccountLockout)
    object_ownership: ObjectOwnershipStore = field(default_factory=ObjectOwnershipStore)
    document_access: InMemoryDocumentAccessStore = field(
        default_factory=InMemoryDocumentAccessStore
    )
    collection_access: InMemoryCollectionAccessStore = field(
        default_factory=InMemoryCollectionAccessStore
    )
    admin_catalog: AdminCatalog | SqliteAdminCatalog = field(
        default_factory=AdminCatalog
    )
    conversations: ConversationStore = field(default_factory=ConversationStore)
    evidence_snapshots: EvidenceSnapshotStore = field(
        default_factory=lambda: InlineEvidenceSnapshotStore(":memory:")
    )
    groups: GroupStore = field(default_factory=GroupStore)
    api_tokens: ApiTokenStore = field(default_factory=InMemoryApiTokenStore)
    oidc: OidcService = field(
        default_factory=lambda: OidcService(
            settings=OidcSettings(),
            verifier=MockOidcProvider(),
        )
    )
    search_index: InMemorySearchIndex = field(default_factory=InMemorySearchIndex)
    analytics: AnalyticsStore = field(default_factory=AnalyticsStore)
    quarantine: QuarantineStore = field(default_factory=QuarantineStore)
    document_actions: BulkDocumentStore = field(default_factory=BulkDocumentStore)
    custom_metadata: CustomMetadataStore = field(default_factory=CustomMetadataStore)
    feedback: FeedbackStore = field(default_factory=FeedbackStore)
    glossary: GlossaryStore = field(default_factory=GlossaryStore)
    metadata_reviews: dict[str, dict[str, str]] = field(default_factory=dict)
    vector_payload_sync: set[str] = field(default_factory=set)
    configured_index: ConfiguredIndexInfo | None = None
    active_index: ActiveIndexInfo | None = None
