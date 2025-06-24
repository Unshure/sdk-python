# Task: Implement Agent State Management with Namespaced Persistence

## Description
Enhance the Strands Agents SDK with a robust agent state management system that enables persistence across application restarts. Replace the current simple `state` dictionary with a comprehensive `AgentState` class that provides flexible namespaced state management, JSON serialization validation, and automatic persistence integration with the session manager.

## Background
The current Strands SDK has a basic `self.state: Dict[str, Any] = {}` placeholder in the Agent class, but lacks proper state management capabilities. Users need to store agent state information that persists across application restarts, including tool execution metadata, dynamic configuration, and conversation management state. The existing session manager infrastructure provides a solid foundation for persistence, but currently only handles message persistence.

## Technical Requirements
1. Create an `AgentState` class with flexible namespaced state management supporting a "default" namespace by default, with ability to create and use any custom namespace names, and a reserved "sdk" namespace for SDK-managed metadata
2. Implement get/set/clear/delete API methods with optional namespace parameters and JSON serialization validation on assignment
3. Extend the Session data model to include a state field for persistence
4. Rename `SessionManager.save_message()` to `update_session()` to save both messages and state together
5. Enhance agent initialization to automatically restore state when session manager is provided
6. Implement SDK namespace auto-population with minimal essential persistence metadata
7. Maintain backward compatibility with existing sessions that don't have state fields
8. Add comprehensive error handling for state operations and persistence failures

## Dependencies
- Existing Agent class with current `state` attribute
- Session data model and SessionManager interface
- JSON serialization infrastructure (`to_dict()`/`from_dict()` pattern)
- Callback handler pattern for persistence triggers
- `initialize_agent_from_session()` method for agent restoration

## Implementation Approach
1. Create `AgentState` class in `src/strands/agent/state.py` with flexible namespace support
2. Extend `Session` dataclass in session models to include state field
3. Update `SessionManager` abstract interface to rename and extend persistence methods
4. Modify Agent class to use new `AgentState` instance instead of simple dictionary
5. Enhance callback handler to trigger state persistence alongside message persistence
6. Update agent initialization logic to restore state from session manager
7. Add comprehensive test coverage for all state management functionality

## Acceptance Criteria

1. **Default Namespace Operations**
   - Given an agent with state management
   - When I call `agent.state.set("key", "value")` with no namespace
   - Then the value is stored in the "default" namespace

2. **Custom Namespace Operations**
   - Given an agent with state management
   - When I call `agent.state.set("key", "value", namespace="custom")`
   - Then the value is stored in the "custom" namespace and the namespace is created if it doesn't exist

3. **Explicit Namespace Creation**
   - Given an agent with state management
   - When I call `agent.state.create_namespace("user_settings")`
   - Then the "user_settings" namespace is created and available for use

4. **JSON Serialization Validation**
   - Given an agent state instance
   - When I attempt to set a non-JSON-serializable value
   - Then a validation error is raised immediately on assignment

5. **Default Namespace Retrieval**
   - Given an agent with state in multiple namespaces
   - When I call `agent.state.get("key")` with no namespace parameter
   - Then I receive the value from the "default" namespace only

6. **Complete Default Namespace Retrieval**
   - Given an agent with state in the default namespace
   - When I call `agent.state.get()` with no parameters
   - Then I receive the entire "default" namespace contents

7. **All Namespaces Retrieval**
   - Given an agent with state in multiple namespaces
   - When I call `agent.state.get_all()`
   - Then I receive the complete state object containing all namespaces

8. **Clear Operations**
   - Given an agent with state in default namespace
   - When I call `agent.state.clear()`
   - Then all data in the "default" namespace is removed

9. **Namespace-Specific Clear Operations**
   - Given an agent with state in a custom namespace
   - When I call `agent.state.clear(namespace="custom")`
   - Then all data in the "custom" namespace is removed

10. **Delete Key Operations**
    - Given an agent with a key in the default namespace
    - When I call `agent.state.delete("key")`
    - Then the specific key is removed from the "default" namespace

11. **Namespace-Specific Delete Operations**
    - Given an agent with a key in a custom namespace
    - When I call `agent.state.delete("key", namespace="custom")`
    - Then the specific key is removed from the "custom" namespace

12. **Namespace Management**
    - Given an agent with multiple namespaces
    - When I call `agent.state.list_namespaces()`
    - Then I receive a list of all existing namespace names

13. **Namespace Existence Check**
    - Given an agent with state management
    - When I call `agent.state.has_namespace("custom")`
    - Then I receive True if the namespace exists, False otherwise

14. **Unified Persistence**
    - Given an agent with session manager and state changes
    - When a message is processed and `update_session()` is called
    - Then both the message and current agent state are persisted together

15. **Automatic State Restoration**
    - Given a saved session with agent state
    - When I create a new agent with the same session manager
    - Then the agent's state is automatically restored from the saved session

16. **SDK Metadata Management**
    - Given an agent with conversation manager
    - When the agent processes messages
    - Then essential persistence metadata is automatically stored in the "sdk" namespace

17. **Backward Compatibility**
    - Given an existing session without state field
    - When I initialize an agent from that session
    - Then the agent initializes successfully with empty state

18. **Error Handling**
    - Given a state persistence failure
    - When the session manager cannot save state
    - Then the error is logged and the agent continues to function

19. **State Isolation**
    - Given state values in different namespaces with the same key
    - When I retrieve values by namespace
    - Then each namespace returns its own value without interference

20. **Reserved SDK Namespace**
    - Given an agent with state management
    - When SDK components store metadata in the "sdk" namespace
    - Then the metadata is properly isolated from user state and persisted correctly

## Metadata
- **Complexity**: High
- **Labels**: Agent, State Management, Persistence, Session Management, JSON Serialization, Namespaces
- **Required Skills**: Python, Object-Oriented Design, Data Persistence, Error Handling
- **Suggested Reviewers**: Someone with experience in state management and persistence patterns
