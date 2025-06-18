"""Abstract interface for conversation history management."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ...agent.agent import Agent
    from ...types.content import Message


class ConversationManager(ABC):
    """Abstract base class for managing conversation history.

    This class provides an interface for implementing conversation management strategies to control the size of message
    arrays/conversation histories, helping to:

    - Manage memory usage
    - Control context length
    - Maintain relevant conversation state
    - Persist conversations to storage (optional)
    """

    @abstractmethod
    # pragma: no cover
    def apply_management(self, agent: "Agent") -> None:
        """Applies management strategy to the provided agent.

        Processes the conversation history to maintain appropriate size by modifying the messages list in-place.
        Implementations should handle message pruning, summarization, or other size management techniques to keep the
        conversation context within desired bounds.

        Args:
            agent: The agent whose conversation history will be manage.
                This list is modified in-place.
        """
        pass

    @abstractmethod
    # pragma: no cover
    def reduce_context(self, agent: "Agent", e: Optional[Exception] = None) -> None:
        """Called when the model's context window is exceeded.

        This method should implement the specific strategy for reducing the window size when a context overflow occurs.
        It is typically called after a ContextWindowOverflowException is caught.

        Implementations might use strategies such as:

        - Removing the N oldest messages
        - Summarizing older context
        - Applying importance-based filtering
        - Maintaining critical conversation markers

        Args:
            agent: The agent whose conversation history will be reduced.
                This list is modified in-place.
            e: The exception that triggered the context reduction, if any.
        """
        pass

    def save_message(self, message: "Message", state: Optional[dict]) -> None:
        """Save a message to the conversation history.

        This method is optional and only needs to be implemented by conversation managers
        that persist conversations to storage.

        Args:
            message: The message to save.
            state: Optional state to save with the message.
        """
        pass

    def load_conversation(self, conversation_id: str, agent_id: str) -> None:
        """Load a conversation from storage.

        This method is optional and only needs to be implemented by conversation managers
        that persist conversations to storage.

        Args:
            conversation_id: The ID of the conversation to load.
            agent_id: The ID of the agent associated with the conversation.
        """
        pass
