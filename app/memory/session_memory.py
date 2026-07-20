# from threading import Lock
# from typing import Dict, List, Optional
# from pydantic import BaseModel


# class ClientProfile(BaseModel):
#     client_name: Optional[str] = None
#     company: Optional[str] = None
#     project_type: Optional[str] = None
#     preferred_technology: Optional[str] = None
#     budget: Optional[str] = None
#     timeline: Optional[str] = None


# class SessionData(BaseModel):
#     profile: ClientProfile = ClientProfile()
#     history: List[Dict[str, str]] = []


# class SessionMemory:
#     def __init__(self) -> None:
#         self._store: Dict[str, SessionData] = {}
#         self._lock = Lock()

#     def get(self, session_id: str) -> SessionData:
#         with self._lock:
#             if session_id not in self._store:
#                 self._store[session_id] = SessionData()
#             return self._store[session_id]

#     def update_profile(self, session_id: str, **kwargs) -> ClientProfile:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             for key, value in kwargs.items():
#                 if value and hasattr(session.profile, key):
#                     setattr(session.profile, key, value)
#             return session.profile

#     def add_message(self, session_id: str, role: str, content: str) -> None:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             session.history.append({"role": role, "content": content})

#     def reset(self, session_id: str) -> None:
#         with self._lock:
#             self._store[session_id] = SessionData()

#     def all_sessions(self) -> Dict[str, SessionData]:
#         return self._store


# session_memory = SessionMemory()


# from threading import Lock
# from typing import Dict, List, Optional
# from pydantic import BaseModel




# class ClientProfile(BaseModel):
#     client_name: Optional[str] = None
#     company: Optional[str] = None
#     project_type: Optional[str] = None
#     preferred_technology: Optional[str] = None
#     budget: Optional[str] = None
#     timeline: Optional[str] = None
#     email: Optional[str] = None
#     meeting_date: Optional[str] = None
#     meeting_time: Optional[str] = None
#     meeting_booked: bool = False




# class SessionData(BaseModel):
#     profile: ClientProfile = ClientProfile()
#     history: List[Dict[str, str]] = []
#     active_agent: Optional[str] = None




# class SessionMemory:
#     def __init__(self) -> None:
#         self._store: Dict[str, SessionData] = {}
#         self._lock = Lock()


#     def get(self, session_id: str) -> SessionData:
#         with self._lock:
#             if session_id not in self._store:
#                 self._store[session_id] = SessionData()
#             return self._store[session_id]


#     def update_profile(self, session_id: str, **kwargs) -> ClientProfile:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             for key, value in kwargs.items():
#                 if value and hasattr(session.profile, key):
#                     setattr(session.profile, key, value)
#             return session.profile


#     def add_message(self, session_id: str, role: str, content: str) -> None:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             session.history.append({"role": role, "content": content})


#     def set_active_agent(self, session_id: str, agent: Optional[str]) -> None:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             session.active_agent = agent


#     def reset(self, session_id: str) -> None:
#         with self._lock:
#             self._store[session_id] = SessionData()


#     def all_sessions(self) -> Dict[str, SessionData]:
#         return self._store




# session_memory = SessionMemory()



# from threading import Lock
# from typing import Dict, List, Optional
# from pydantic import BaseModel




# class ClientProfile(BaseModel):
#     client_name: Optional[str] = None
#     company: Optional[str] = None
#     project_type: Optional[str] = None
#     preferred_technology: Optional[str] = None
#     budget: Optional[str] = None
#     timeline: Optional[str] = None
#     email: Optional[str] = None
#     meeting_date: Optional[str] = None
#     meeting_time: Optional[str] = None
#     meeting_booked: bool = False




# class SessionData(BaseModel):
#     profile: ClientProfile = ClientProfile()
#     history: List[Dict[str, str]] = []
#     active_agent: Optional[str] = None




# class SessionMemory:
#     def __init__(self) -> None:
#         self._store: Dict[str, SessionData] = {}
#         self._lock = Lock()


#     def get(self, session_id: str) -> SessionData:
#         with self._lock:
#             if session_id not in self._store:
#                 self._store[session_id] = SessionData()
#             return self._store[session_id]


#     def update_profile(self, session_id: str, **kwargs) -> ClientProfile:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             # NOTE: this is always called with the *complete* merged profile
#             # for the turn (built from session.profile.model_dump() and then
#             # mutated by the graph), not a partial delta. So we must apply
#             # every known field as-is, including falsy ones (None/False) —
#             # otherwise a field can be set but never cleared, which breaks
#             # resetting the Meeting Agent's state after a booking completes.
#             for key, value in kwargs.items():
#                 if hasattr(session.profile, key):
#                     setattr(session.profile, key, value)
#             return session.profile


#     def add_message(self, session_id: str, role: str, content: str) -> None:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             session.history.append({"role": role, "content": content})


#     def set_active_agent(self, session_id: str, agent: Optional[str]) -> None:
#         with self._lock:
#             session = self._store.setdefault(session_id, SessionData())
#             session.active_agent = agent


#     def reset(self, session_id: str) -> None:
#         with self._lock:
#             self._store[session_id] = SessionData()


#     def all_sessions(self) -> Dict[str, SessionData]:
#         return self._store




# session_memory = SessionMemory()

from threading import Lock
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extras import Json
from pydantic import BaseModel

from app.config import settings
from app.logging_config import logger




class ClientProfile(BaseModel):
    client_name: Optional[str] = None
    company: Optional[str] = None
    project_type: Optional[str] = None
    preferred_technology: Optional[str] = None
    budget: Optional[str] = None
    timeline: Optional[str] = None
    email: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_time: Optional[str] = None
    meeting_booked: bool = False




class SessionData(BaseModel):
    profile: ClientProfile = ClientProfile()
    history: List[Dict[str, str]] = []
    active_agent: Optional[str] = None




class SessionMemory:
    """Same public API as the previous in-memory version (get, update_profile,
    add_message, set_active_agent, reset, all_sessions), now backed by
    PostgreSQL so sessions survive a server restart. Uses the project's
    existing psycopg2 + settings.DATABASE_URL pattern (see app/rag/vector_store.py)
    rather than introducing a second DB access style."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._conn = psycopg2.connect(settings.DATABASE_URL)
        self._conn.autocommit = True
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    profile JSONB NOT NULL DEFAULT '{}'::jsonb,
                    active_agent TEXT,
                    history JSONB NOT NULL DEFAULT '[]'::jsonb,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
        logger.info("Session store (PostgreSQL) ready: chat_sessions table ensured")

    def _load(self, session_id: str) -> Optional[SessionData]:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT profile, active_agent, history FROM chat_sessions WHERE session_id = %s;",
                (session_id,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        profile_json, active_agent, history_json = row
        return SessionData(
            profile=ClientProfile(**(profile_json or {})),
            active_agent=active_agent,
            history=history_json or [],
        )

    def _save(self, session_id: str, session: SessionData) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (session_id, profile, active_agent, history, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (session_id) DO UPDATE SET
                    profile = EXCLUDED.profile,
                    active_agent = EXCLUDED.active_agent,
                    history = EXCLUDED.history,
                    updated_at = now();
                """,
                (
                    session_id,
                    Json(session.profile.model_dump()),
                    session.active_agent,
                    Json(session.history),
                ),
            )

    def get(self, session_id: str) -> SessionData:
        with self._lock:
            session = self._load(session_id)
            if session is None:
                session = SessionData()
                self._save(session_id, session)
            return session

    def update_profile(self, session_id: str, **kwargs) -> ClientProfile:
        with self._lock:
            session = self._load(session_id) or SessionData()
            # NOTE: intentionally no truthy-filtering here — the caller
            # (graph.py) always passes the complete, authoritative profile
            # for the turn, and fields like meeting_booked/email must be
            # allowed to be explicitly cleared (set back to None/False) once
            # a meeting is booked, not just set.
            for key, value in kwargs.items():
                if hasattr(session.profile, key):
                    setattr(session.profile, key, value)
            self._save(session_id, session)
            return session.profile

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            session = self._load(session_id) or SessionData()
            session.history.append({"role": role, "content": content})
            self._save(session_id, session)

    def set_active_agent(self, session_id: str, agent: Optional[str]) -> None:
        with self._lock:
            session = self._load(session_id) or SessionData()
            session.active_agent = agent
            self._save(session_id, session)

    def reset(self, session_id: str) -> None:
        with self._lock:
            self._save(session_id, SessionData())

    def all_sessions(self) -> Dict[str, SessionData]:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute("SELECT session_id, profile, active_agent, history FROM chat_sessions;")
                rows = cur.fetchall()
        return {
            session_id: SessionData(
                profile=ClientProfile(**(profile_json or {})),
                active_agent=active_agent,
                history=history_json or [],
            )
            for session_id, profile_json, active_agent, history_json in rows
        }




session_memory = SessionMemory()