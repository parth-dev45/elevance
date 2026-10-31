"""
Task 6: Multi-Tenant Session Isolation, Context Window & Lifecycle Manager.
Retains 10+ message history, enforces 30-min inactivity expiry,
and restores conversation summary when customer returns within 24 hours.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from pydantic import BaseModel, Field
from core.time_engine import time_engine
from core.config import config
from core.logger import audit_logger
from core.security import security_service

class SessionTurn(BaseModel):
    role: str # user, assistant, system
    content: str
    sentiment: Optional[str] = None
    language: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: time_engine.now())

class CustomerSession(BaseModel):
    session_id: str
    customer_id: str
    language: str = "en"
    history: List[SessionTurn] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    last_activity_at: datetime
    is_active: bool = True
    closed_at: Optional[datetime] = None
    conversation_summary: Optional[str] = None

class SessionManager:
    def __init__(self):
        # Maps session_id -> CustomerSession
        self.active_sessions: Dict[str, CustomerSession] = {}
        # Maps customer_id -> List[CustomerSession] (history of past sessions)
        self.customer_history: Dict[str, List[CustomerSession]] = {}

    def get_or_create_session(self, customer_id: str) -> Tuple[CustomerSession, str]:
        """
        Retrieves active session or creates a new one enforcing:
        1. 30-min inactivity timeout (auto-closes inactive session).
        2. 24-hr returning customer restoration (restores summary if < 24h).
        3. Fresh session if > 24h.
        4. Strict multi-tenant session isolation.
        Returns: (session, status_action: 'EXISTING_ACTIVE' | 'RESTORED_PREVIOUS_SUMMARY' | 'FRESH_SESSION')
        """
        now = time_engine.now()
        inactivity_limit_seconds = config.session_inactivity_minutes * 60.0 # 30 mins (1800s)
        restore_limit_seconds = config.session_restore_window_hours * 3600.0 # 24 hours (86400s)

        # 1. Check for existing active session for this customer
        active_session = None
        for sess in self.active_sessions.values():
            if sess.customer_id == customer_id and sess.is_active:
                active_session = sess
                break

        if active_session:
            # Check for 30-minute inactivity expiry
            idle_seconds = (now - active_session.last_activity_at).total_seconds()
            if idle_seconds > inactivity_limit_seconds:
                # Close this session due to inactivity
                self.close_session(active_session.session_id, reason=f"Inactivity timeout ({round(idle_seconds/60, 1)}m > 30m)")
                active_session = None
            else:
                # Active session continues
                active_session.last_activity_at = now
                return active_session, "EXISTING_ACTIVE"

        # 2. Check past closed sessions for this customer to determine if returning within 24h
        past_sessions = self.customer_history.get(customer_id, [])
        restored_summary = None
        status_action = "FRESH_SESSION"

        if past_sessions:
            last_closed_session = past_sessions[-1]
            if last_closed_session.closed_at:
                time_since_closed = (now - last_closed_session.closed_at).total_seconds()
                if time_since_closed <= restore_limit_seconds:
                    # Customer returned within 24 hours: restore conversation summary
                    restored_summary = last_closed_session.conversation_summary
                    status_action = "RESTORED_PREVIOUS_SUMMARY"
                    audit_logger.log("INFO", f"Customer '{customer_id}' returned within {round(time_since_closed/3600, 1)}h (<24h). Restoring previous session summary.")

        # 3. Create new isolated session
        new_session_id = f"SES-{customer_id[:6].upper()}-{uuid.uuid4().hex[:6].upper()}"
        new_session = CustomerSession(
            session_id=new_session_id,
            customer_id=customer_id,
            created_at=now,
            last_activity_at=now,
            is_active=True,
            conversation_summary=restored_summary
        )

        if restored_summary:
            # Seed system turn with previous context summary
            new_session.history.append(
                SessionTurn(
                    role="system",
                    content=f"[RESTORED CONVERSATION SUMMARY FROM PREVIOUS SESSION]: {restored_summary}",
                    timestamp=now
                )
            )

        self.active_sessions[new_session_id] = new_session
        audit_logger.log("INFO", f"Created session '{new_session_id}' for customer '{customer_id}'. Status: {status_action}")
        return new_session, status_action

    def add_message(self, session_id: str, role: str, content: str,
                    sentiment: Optional[str] = None, language: Optional[str] = None):
        """Adds a turn to session history, guaranteeing retention of at least 10 messages."""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.last_activity_at = time_engine.now()
        session.history.append(
            SessionTurn(
                role=role,
                content=content,
                sentiment=sentiment,
                language=language,
                timestamp=session.last_activity_at
            )
        )

        # Retain at least 15 messages in memory context
        if len(session.history) > 25:
            # Keep system summary if present
            has_summary = session.history[0].role == "system"
            if has_summary:
                session.history = [session.history[0]] + session.history[-15:]
            else:
                session.history = session.history[-15:]

    def close_session(self, session_id: str, reason: str = "Manual close"):
        """Closes session, generates masked summary, and moves to customer history."""
        if session_id not in self.active_sessions:
            return

        session = self.active_sessions[session_id]
        session.is_active = False
        session.closed_at = time_engine.now()

        # Generate summary of conversation
        turns = [f"{t.role}: {t.content}" for t in session.history if t.role != "system"]
        raw_summary = " | ".join(turns) if turns else "No messages exchanged."
        session.conversation_summary = security_service.mask_pii(f"Prior discussion: {raw_summary[:300]}")

        # Archive into customer history
        if session.customer_id not in self.customer_history:
            self.customer_history[session.customer_id] = []
        self.customer_history[session.customer_id].append(session)

        del self.active_sessions[session_id]
        audit_logger.log("INFO", f"Closed session '{session_id}'. Reason: {reason}. Summary generated.")

session_manager = SessionManager()
