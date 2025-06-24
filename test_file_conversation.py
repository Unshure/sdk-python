"""Test script for FileConversationManager integration."""

from strands import Agent
from strands.session.default_session_manager import DefaultSessionManager

session_manager = DefaultSessionManager()

# Create an agent with the file conversation manager
agent = Agent(session_manager=session_manager)

while True:
    agent(input("\nInput: "))
