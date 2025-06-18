import os
import json
import shutil
import unittest
from pathlib import Path
from typing import List, Optional

from ...types.content import Message, ContentBlock
from .file_conversation_manager import FileConversationManager


class TestFileConversationManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test conversations
        self.test_dir = os.path.join(os.getcwd(), "test_conversations")
        os.makedirs(self.test_dir, exist_ok=True)
        self.manager = FileConversationManager(storage_dir=self.test_dir)

        # Set up test data
        self.conversation_id = "test-conversation-123"
        self.agent_id = "test-agent-456"

        # Create a test message
        self.test_message = {"role": "user", "content": [{"text": "Hello, this is a test message"}]}

        # Create a test state
        self.test_state = {"key": "value", "counter": 42}

    def tearDown(self):
        # Clean up the test directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_and_load_message(self):
        # Initialize the conversation
        self.manager.load_conversation(self.conversation_id, self.agent_id)

        # Save a message
        self.manager.save_message(self.test_message, self.test_state)

        # Check that the file was created
        file_path = os.path.join(self.test_dir, f"{self.conversation_id}.json")
        self.assertTrue(os.path.exists(file_path))

        # Create a new manager to test loading
        new_manager = FileConversationManager(storage_dir=self.test_dir)
        new_manager.load_conversation(self.conversation_id, self.agent_id)

        # Check that the message was loaded correctly
        self.assertEqual(len(new_manager.messages), 1)
        self.assertEqual(new_manager.messages[0], self.test_message)
        self.assertEqual(new_manager.state, self.test_state)
        self.assertEqual(new_manager.conversation_id, self.conversation_id)
        self.assertEqual(new_manager.agent_id, self.agent_id)

    def test_multiple_messages(self):
        # Initialize the conversation
        self.manager.load_conversation(self.conversation_id, self.agent_id)

        # Save multiple messages
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
            {"role": "user", "content": [{"text": "How are you?"}]},
            {"role": "assistant", "content": [{"text": "I'm doing well, thank you!"}]},
        ]

        for message in messages:
            self.manager.save_message(message, self.test_state)

        # Create a new manager to test loading
        new_manager = FileConversationManager(storage_dir=self.test_dir)
        new_manager.load_conversation(self.conversation_id, self.agent_id)

        # Check that all messages were loaded correctly
        self.assertEqual(len(new_manager.messages), len(messages))
        for i, message in enumerate(messages):
            self.assertEqual(new_manager.messages[i], message)

    def test_nonexistent_conversation(self):
        # Try to load a conversation that doesn't exist
        self.manager.load_conversation("nonexistent-conversation", self.agent_id)

        # Check that the messages list is empty
        self.assertEqual(len(self.manager.messages), 0)

    def test_save_without_initialization(self):
        # Create a new manager without initializing a conversation
        new_manager = FileConversationManager(storage_dir=self.test_dir)

        # Try to save a message without initializing the conversation
        with self.assertRaises(ValueError):
            new_manager.save_message(self.test_message, self.test_state)


if __name__ == "__main__":
    unittest.main()
