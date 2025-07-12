"""Session manager interface for agent session management."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..hooks.events import AfterInvocationEvent, AgentInitializedEvent, MessageAddedEvent
from ..hooks.registry import HookProvider, HookRegistry
from ..types.content import Message

if TYPE_CHECKING:
    from ..agent.agent import Agent


class SessionManager(HookProvider, ABC):
    """Abstract interface for managing sessions.

    A session represents a complete interaction context including conversation
    history, user information, agent state, and metadata. This interface provides
    methods to manage sessions and their associated data.
    """

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        """Register initialize and append_message as hooks for the Agent."""
        registry.add_callback(AgentInitializedEvent, lambda event: self.initialize(event.agent))
        registry.add_callback(MessageAddedEvent, lambda event: self.append_message(event.message, event.agent))
        registry.add_callback(MessageAddedEvent, lambda event: self.persist_agent(event.agent))
        registry.add_callback(AfterInvocationEvent, lambda event: self.persist_agent(event.agent))

    @abstractmethod
    def append_message(self, message: Message, agent: "Agent") -> None:
        """Append a message to the agent's session.

        Args:
            message: Message to append to the session's agent
            agent: Agent to appent the message to
        """

    @abstractmethod
    def persist_agent(self, agent: "Agent") -> None:
        """Persist the agent in the session.

        Args:
            agent: Agent to update in the session
        """

    @abstractmethod
    def initialize(self, agent: "Agent") -> None:
        """Initialize an agent with a session.

        Args:
            agent: Agent to update in the session
        """
