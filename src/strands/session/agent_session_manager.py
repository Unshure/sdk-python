"""Agent session manager implementation."""

import logging

from ..agent.agent import Agent
from ..agent.state import AgentState
from ..telemetry.metrics import EventLoopMetrics
from ..types.content import Message
from ..types.session import (
    SessionType,
    create_session,
    session_agent_from_agent,
    session_message_from_message,
    session_message_to_message,
)
from .session_manager import SessionManager
from .session_repository import SessionRepository

logger = logging.getLogger(__name__)

DEFAULT_SESSION_AGENT_ID = "default"


class AgentSessionManager(SessionManager):
    """Session manager for persisting agent's in a Session."""

    def __init__(
        self,
        session_id: str,
        session_repository: SessionRepository,
    ):
        """Initialize the AgentSessionManager."""
        self.session_repository = session_repository
        self.session_id = session_id
        session = session_repository.read_session(session_id)
        # Create a session if it does not exist yet
        if session is None:
            logger.debug("session_id=<%s> | Session not found, creating new session.", self.session_id)
            session = create_session(session_id=session_id, session_type=SessionType.AGENT)
            session_repository.create_session(session)

        self.session = session
        self._default_agent_initialized = False

    def append_message(self, message: Message, agent: Agent) -> None:
        """Append a message to the agent's session."""
        if agent.agent_id is None:
            raise ValueError("`agent.agent_id` must be set before appending message to session.")

        session_message = session_message_from_message(message)
        self.session_repository.create_message(self.session_id, agent.agent_id, session_message)

    def persist_agent(self, agent: Agent) -> None:
        """Persist the agent to the session.

        Args:
            agent: Agent to update in the session
        """
        self.session_repository.update_agent(
            self.session_id,
            session_agent_from_agent(agent=agent),
        )

    def initialize(self, agent: Agent) -> None:
        """Initialize an agent with a session."""
        if agent.agent_id is None:
            if self._default_agent_initialized:
                raise ValueError(
                    "By default, only one agent with no `agent_id` can be initialized within session_manager."
                    "Set `agent_id` to support more than one agent in a session."
                )
            logger.debug(
                "agent_id=<%s> | session_id=<%s> | Using default agent_id.",
                agent.agent_id,
                self.session_id,
            )
            agent.agent_id = DEFAULT_SESSION_AGENT_ID
            self._default_agent_initialized = True

        session_agent = self.session_repository.read_agent(self.session_id, agent.agent_id)

        if session_agent is None:
            logger.debug(
                "agent_id=<%s> | session_id=<%s> | Creating agent.",
                agent.agent_id,
                self.session_id,
            )

            session_agent = session_agent_from_agent(agent)
            self.session_repository.create_agent(self.session_id, session_agent)
            for message in agent.messages:
                session_message = session_message_from_message(message)
                self.session_repository.create_message(self.session_id, agent.agent_id, session_message)
        else:
            logger.debug(
                "agent_id=<%s> | session_id=<%s> | Restoring agent.",
                agent.agent_id,
                self.session_id,
            )
            agent.state = AgentState(session_agent["state"])
            agent.event_loop_metrics = EventLoopMetrics.from_dict(session_agent["event_loop_metrics"])
            # Initialize the agent with all of the messages from its past conversation
            agent.messages = [
                session_message_to_message(session_message)
                for session_message in self.session_repository.list_messages(self.session_id, agent.agent_id)
            ]
            print(agent.messages)
            # Restore the conversation manager state, and restore the agent's messages array to its previous state
            agent.conversation_manager.restore_from_state(session_agent["conversation_manager_state"], agent)
