# Implementation Prompt Plan

## Checklist
- [x] Prompt 1: Create persistence exception classes and base interface
- [x] Prompt 2: Implement FilePersistenceManager with file operations
- [x] Prompt 3: Create PersistenceCallbackHandler for automatic state saving
- [x] Prompt 4: Extend Agent class with persistence integration
- [x] Prompt 5: Add customer state management methods to Agent
- [x] Prompt 6: Implement automatic state restoration logic
- [x] Prompt 7: Create comprehensive unit tests for persistence components
- [ ] Prompt 8: Add integration tests for end-to-end persistence workflow
- [ ] Prompt 9: Update Agent constructor and callback integration
- [ ] Prompt 10: Wire everything together and test complete functionality

## Prompts

### Prompt 1: Create persistence exception classes and base interface

Create the foundational persistence infrastructure by implementing the exception classes and abstract PersistenceManager interface.

1. Create `src/strands/persistence/__init__.py` module with exports
2. Create `src/strands/persistence/exceptions.py` with PersistenceException class
3. Create `src/strands/persistence/persistence_manager.py` with the abstract PersistenceManager interface
4. Implement all abstract methods as defined in the design document with proper type hints
5. Add comprehensive docstrings following the existing codebase patterns
6. Create basic unit tests to verify the interface structure

Focus on establishing clean interfaces and proper error handling foundations. The abstract methods should raise NotImplementedError and include detailed docstrings that will guide the concrete implementations.

### Prompt 2: Implement FilePersistenceManager with file operations

Implement the file-based persistence manager that handles JSON storage operations.

1. Create `src/strands/persistence/file_persistence_manager.py` 
2. Implement FilePersistenceManager class extending PersistenceManager
3. Add constructor with configurable storage directory (defaulting to temp directory)
4. Implement all persistence methods: save_agent_state, save_customer_state, save_request_state
5. Implement all load methods: load_agent_state, load_customer_state, load_request_state
6. Add session management methods: delete_session, session_exists
7. Include proper error handling with PersistenceException wrapping
8. Add helper methods for directory management and file path generation
9. Handle EventLoopMetrics serialization using dataclasses.asdict()
10. Create unit tests covering all methods, error conditions, and edge cases

Ensure atomic file operations where possible and robust error handling for file system issues. Test with various data types and sizes to verify JSON serialization works correctly.

### Prompt 3: Create PersistenceCallbackHandler for automatic state saving

Implement the callback handler that integrates persistence with the agent's event system.

1. Create `src/strands/persistence/persistence_callback_handler.py`
2. Implement PersistenceCallbackHandler class with session identification
3. Add __call__ method that handles various callback events
4. Implement logic to save agent state when "message" events occur
5. Add handling for request state persistence when metrics and stop_reason are available
6. Include customer state persistence when state updates occur
7. Add proper error handling and logging for persistence failures
8. Create unit tests that mock the persistence manager and verify correct method calls
9. Test various callback event scenarios and edge cases

Focus on making the callback handler robust and ensuring it doesn't interfere with normal agent operation even if persistence fails.

### Prompt 4: Extend Agent class with persistence integration

Modify the existing Agent class to support persistence functionality.

1. Add persistence-related parameters to Agent.__init__: persistence_manager, session_id, agent_id, user_id
2. Add customer_state attribute as Dict[str, Any] initialized to empty dict
3. Integrate persistence_manager into the agent's initialization process
4. Add logic to create PersistenceCallbackHandler when persistence is enabled
5. Integrate persistence callback with existing CompositeCallbackHandler pattern
6. Add validation for required session identifiers when persistence is enabled
7. Ensure backward compatibility - all new parameters should be optional
8. Add proper type hints and docstring updates for new parameters
9. Create unit tests for the new initialization logic

Make sure the integration doesn't break existing functionality and follows the established patterns in the Agent class.

### Prompt 5: Add customer state management methods to Agent

Implement customer state management functionality in the Agent class.

1. Add update_customer_state(updates: Dict[str, Any]) method to Agent class
2. Add get_customer_state() method that returns a copy of current state
3. Add clear_session() method to delete all persisted data
4. Ensure customer state updates trigger persistence automatically
5. Add proper error handling for persistence failures in state updates
6. Include comprehensive docstrings explaining the customer state functionality
7. Add validation for customer state data (must be JSON serializable)
8. Create unit tests for all customer state management methods
9. Test integration with persistence manager

Focus on providing a clean API for customer state management while ensuring automatic persistence works correctly.

### Prompt 6: Implement automatic state restoration logic

Add automatic state restoration functionality to the Agent class.

1. Create _restore_persisted_state() private method in Agent class
2. Implement logic to load and restore conversation history (messages)
3. Add customer state restoration from persistence
4. Include proper error handling that re-raises PersistenceException as required
5. Add validation to ensure restoration only happens when all identifiers are provided
6. Integrate restoration call into Agent.__init__ when persistence is enabled
7. Add logging for successful and failed restoration attempts
8. Create unit tests covering successful restoration, missing data, and error scenarios
9. Test that restored state integrates properly with agent functionality

Ensure restoration is robust and handles various edge cases like missing files or corrupted data appropriately.

### Prompt 7: Create comprehensive unit tests for persistence components

Develop thorough unit tests for all persistence components.

1. Create `tests/persistence/test_persistence_manager.py` for interface tests
2. Create `tests/persistence/test_file_persistence_manager.py` for file implementation tests
3. Create `tests/persistence/test_persistence_callback_handler.py` for callback tests
4. Add tests for all CRUD operations with various data types and sizes
5. Include error condition tests: file system errors, corrupted data, permission issues
6. Test session management functionality: creation, deletion, existence checks
7. Add tests for EventLoopMetrics serialization and deserialization
8. Include edge case tests: empty data, large datasets, special characters
9. Mock file system operations where appropriate to test error handling
10. Ensure high test coverage (>90%) for all persistence components

Focus on testing both happy path and error scenarios to ensure robust operation.

### Prompt 8: Add integration tests for end-to-end persistence workflow

Create integration tests that verify the complete persistence workflow.

1. Create `tests/integration/test_agent_persistence.py` for end-to-end tests
2. Test complete agent lifecycle: create, interact, persist, restart, restore
3. Add tests for conversation continuity across agent restarts
4. Test customer state persistence and restoration
5. Include request state tracking and restoration scenarios
6. Add tests for multiple sessions with different identifiers
7. Test error scenarios: corrupted files, missing permissions, disk full
8. Include performance tests with large conversation histories
9. Test integration with existing ConversationManager functionality
10. Verify backward compatibility with agents that don't use persistence

These tests should simulate real-world usage patterns and verify that persistence works seamlessly.

### Prompt 9: Update Agent constructor and callback integration

Finalize the Agent class integration with proper callback handling.

1. Update Agent.__init__ to properly integrate persistence callback with existing callbacks
2. Ensure CompositeCallbackHandler correctly chains persistence with user callbacks
3. Add logic to pass necessary context (messages, customer_state) to persistence callbacks
4. Update callback invocations throughout Agent methods to include persistence data
5. Add session identifier validation and helpful error messages
6. Include proper handling of None values for optional persistence parameters
7. Update existing callback invocations to support persistence context
8. Add comprehensive docstring updates explaining persistence functionality
9. Create tests for callback integration and chaining
10. Test various callback handler combinations and configurations

Ensure the callback integration is seamless and doesn't interfere with existing callback functionality.

### Prompt 10: Wire everything together and test complete functionality

Complete the implementation by integrating all components and conducting final testing.

1. Update `src/strands/persistence/__init__.py` to export all public classes
2. Update main `src/strands/__init__.py` to include persistence exports
3. Create example usage documentation showing how to use persistence features
4. Add comprehensive integration tests covering all persistence scenarios
5. Test with various storage directories and configurations
6. Verify error handling works correctly across all components
7. Test performance with realistic data sizes and usage patterns
8. Add logging and debugging support for persistence operations
9. Create migration guide for users wanting to add persistence to existing agents
10. Conduct final end-to-end testing with complete workflow scenarios

Focus on ensuring everything works together seamlessly and the API is intuitive for users. Test edge cases and verify that the implementation meets all original requirements.

## Examples

### Example Usage After Implementation

```python
from strands import Agent
from strands.persistence import FilePersistenceManager

# Create persistence manager
persistence = FilePersistenceManager(storage_dir="/path/to/storage")

# Create agent with persistence
agent = Agent(
    model="claude-3-sonnet",
    persistence_manager=persistence,
    session_id="user_session_123",
    agent_id="my_agent",
    user_id="user_456"
)

# Use agent normally - persistence happens automatically
response = agent("Hello, how are you?")

# Update customer state
agent.update_customer_state({"preference": "concise", "language": "en"})

# Agent state is automatically persisted and will be restored on next initialization
```

### Example File Structure After Implementation

```
src/strands/persistence/
├── __init__.py
├── exceptions.py
├── persistence_manager.py
├── file_persistence_manager.py
└── persistence_callback_handler.py

tests/persistence/
├── test_persistence_manager.py
├── test_file_persistence_manager.py
└── test_persistence_callback_handler.py

tests/integration/
└── test_agent_persistence.py
```

## Troubleshooting

### Common Implementation Issues

**File System Permissions**: Ensure proper error handling for permission denied scenarios and provide helpful error messages.

**JSON Serialization**: Test with complex data structures and handle serialization edge cases properly.

**Callback Integration**: Verify that persistence callbacks don't interfere with existing callback functionality.

**State Restoration**: Handle cases where partial state exists or data is corrupted gracefully.

**Performance**: Monitor file I/O performance with large datasets and optimize if necessary.
