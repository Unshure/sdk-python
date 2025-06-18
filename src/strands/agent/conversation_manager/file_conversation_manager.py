import json
import os
from typing import TYPE_CHECKING, List, Optional, TypedDict
from uuid import uuid4

from .conversation_manager import ConversationManager

if TYPE_CHECKING:
    from ...agent.agent import Agent
    from ...types.content import Message


class Conversation(TypedDict):
    conversation_id: str
    agent_id: str
    messages: List["Message"]
    state: Optional[dict]


class FileConversationManager(ConversationManager):
    """A conversation manager that persists conversations to files.

    This implementation saves conversations to JSON files in a specified directory.
    Each conversation is stored in a separate file named by its conversation_id.
    """

    def __init__(self, storage_dir: str = None):
        """Initialize the FileConversationManager.

        Args:
            storage_dir: Directory where conversation files will be stored.
                If None, defaults to a 'conversations' directory in the current working directory.
        """
        super().__init__()
        self.messages = []
        self.storage_dir = storage_dir or os.path.join(os.getcwd(), "conversations")
        self.conversation_id = str(uuid4())
        self.agent_id = f"agent_{str(uuid4())[:8]}"
        self.state = None

        # Create the storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_file_path(self, conversation_id: str) -> str:
        """Get the file path for a conversation.

        Args:
            conversation_id: The ID of the conversation.

        Returns:
            The file path for the conversation.
        """
        return os.path.join(self.storage_dir, f"{conversation_id}.json")

    def _save_message_to_db(self, message: "Message", state: Optional[dict]) -> None:
        """Save a message to the conversation file.

        Args:
            message: The message to save.
            state: Optional state to save with the message.
        """
        if not self.conversation_id or not self.agent_id:
            raise ValueError("Conversation ID and agent ID must be set before saving messages")

        # Add the message to the in-memory list
        self.messages.append(message)
        self.state = state

        # Save the entire conversation to the file
        conversation = {
            "conversation_id": self.conversation_id,
            "agent_id": self.agent_id,
            "messages": self.messages,
            "state": self.state,
        }

        file_path = self._get_file_path(self.conversation_id)

        try:
            with open(file_path, "w") as f:
                json.dump(conversation, f, indent=2)
        except Exception as e:
            raise IOError(f"Failed to save conversation to file: {e}")

    def _load_messages_from_db(self, conversation_id: str) -> List["Message"]:
        """Load messages from a conversation file.

        Args:
            conversation_id: The ID of the conversation to load.

        Returns:
            A list of messages from the conversation.

        Raises:
            FileNotFoundError: If the conversation file doesn't exist.
        """
        file_path = self._get_file_path(conversation_id)

        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r") as f:
                conversation = json.load(f)

            # Update the conversation state
            self.conversation_id = conversation.get("conversation_id")
            self.agent_id = conversation.get("agent_id")
            self.state = conversation.get("state")

            return conversation.get("messages", [])
        except Exception as e:
            raise IOError(f"Failed to load conversation from file: {e}")

    def load_conversation(self, conversation_id: str, agent_id: str) -> None:
        """Load a conversation from a file.

        Args:
            conversation_id: The ID of the conversation to load.
            agent_id: The ID of the agent associated with the conversation.
        """
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.messages = self._load_messages_from_db(conversation_id)

    def save_message(self, message: "Message", state: Optional[dict]) -> None:
        """Save a message to the current conversation.

        Args:
            message: The message to save.
            state: Optional state to save with the message.
        """
        # Check if this message is a duplicate of the last message
        if self.messages and self._messages_are_equal(message, self.messages[-1]):
            # Skip saving duplicate messages
            return

        self._save_message_to_db(message, state)

    def _messages_are_equal(self, message1: "Message", message2: "Message") -> bool:
        """Check if two messages are equal.

        Args:
            message1: First message to compare
            message2: Second message to compare

        Returns:
            True if the messages are equal, False otherwise
        """
        # Check if roles are equal
        if message1.get("role") != message2.get("role"):
            return False

        # Check if content lengths are equal
        content1 = message1.get("content", [])
        content2 = message2.get("content", [])
        if len(content1) != len(content2):
            return False

        # Check if content items are equal
        for i in range(len(content1)):
            item1 = content1[i]
            item2 = content2[i]

            # Check if item types are equal
            if set(item1.keys()) != set(item2.keys()):
                return False

            # Check if text content is equal
            if "text" in item1 and "text" in item2:
                if item1["text"] != item2["text"]:
                    return False

            # Check if toolUse content is equal
            if "toolUse" in item1 and "toolUse" in item2:
                tool_use1 = item1["toolUse"]
                tool_use2 = item2["toolUse"]

                if tool_use1.get("name") != tool_use2.get("name"):
                    return False

                if tool_use1.get("input") != tool_use2.get("input"):
                    return False

            # Check if toolResult content is equal
            if "toolResult" in item1 and "toolResult" in item2:
                tool_result1 = item1["toolResult"]
                tool_result2 = item2["toolResult"]

                if tool_result1.get("toolUseId") != tool_result2.get("toolUseId"):
                    return False

                if tool_result1.get("status") != tool_result2.get("status"):
                    return False

                result_content1 = tool_result1.get("content", [])
                result_content2 = tool_result2.get("content", [])

                if len(result_content1) != len(result_content2):
                    return False

                for j in range(len(result_content1)):
                    if result_content1[j].get("text") != result_content2[j].get("text"):
                        return False

        return True

    def apply_management(self, agent: "Agent") -> None:
        """Applies management strategy to the provided agent.

        This implementation does not modify the agent's messages.

        Args:
            agent: The agent whose conversation history will be managed.
        """
        pass

    def reduce_context(self, agent: "Agent", e: Optional[Exception] = None) -> None:
        """Called when the model's context window is exceeded.

        This implementation does not modify the agent's messages.

        Args:
            agent: The agent whose conversation history will be reduced.
            e: The exception that triggered the context reduction, if any.
        """
        pass
