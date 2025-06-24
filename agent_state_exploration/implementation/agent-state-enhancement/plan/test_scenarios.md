# Agent State Enhancement - Test Scenarios

## AgentState Class Tests

### Namespace Operations
1. **Default Namespace Set/Get**
   - Input: `state.set("key", "value")`
   - Expected: Value stored in "default" namespace
   - Verification: `state.get("key")` returns "value"

2. **Custom Namespace Set/Get**
   - Input: `state.set("key", "value", namespace="custom")`
   - Expected: Value stored in "custom" namespace, namespace created if needed
   - Verification: `state.get("key", namespace="custom")` returns "value"

3. **Namespace Isolation**
   - Input: Set same key in different namespaces
   - Expected: Values remain separate per namespace
   - Verification: Each namespace returns its own value

### JSON Serialization Validation
4. **Valid JSON Values**
   - Input: String, int, float, bool, list, dict
   - Expected: All values accepted and stored
   - Verification: Values retrievable without modification

5. **Invalid JSON Values**
   - Input: Custom objects, functions, complex types
   - Expected: ValidationError raised immediately
   - Verification: Exception contains helpful error message

### Retrieval Operations
6. **Single Key Retrieval**
   - Input: `state.get("existing_key")`
   - Expected: Returns stored value
   - Verification: Correct value returned

7. **Missing Key Retrieval**
   - Input: `state.get("nonexistent_key")`
   - Expected: Returns None
   - Verification: No exception raised

8. **Entire Namespace Retrieval**
   - Input: `state.get()` (no key parameter)
   - Expected: Returns entire default namespace dict
   - Verification: All default namespace contents returned

9. **All Namespaces Retrieval**
   - Input: `state.get_all()`
   - Expected: Returns dict with all namespaces
   - Verification: Complete state structure returned

### Clear Operations
10. **Clear Default Namespace**
    - Input: `state.clear()`
    - Expected: Default namespace emptied
    - Verification: Default namespace is empty dict

11. **Clear Custom Namespace**
    - Input: `state.clear(namespace="custom")`
    - Expected: Custom namespace emptied
    - Verification: Custom namespace is empty dict

### Delete Operations
12. **Delete Key from Default**
    - Input: `state.delete("key")`
    - Expected: Key removed from default namespace
    - Verification: Key no longer exists in default

13. **Delete Key from Custom Namespace**
    - Input: `state.delete("key", namespace="custom")`
    - Expected: Key removed from custom namespace
    - Verification: Key no longer exists in custom namespace

14. **Delete Nonexistent Key**
    - Input: `state.delete("nonexistent")`
    - Expected: No error, operation is idempotent
    - Verification: No exception raised

### Namespace Management
15. **Create Namespace**
    - Input: `state.create_namespace("new_ns")`
    - Expected: Namespace created and available
    - Verification: `state.has_namespace("new_ns")` returns True

16. **List Namespaces**
    - Input: `state.list_namespaces()`
    - Expected: Returns list of all namespace names
    - Verification: All created namespaces included

17. **Check Namespace Existence**
    - Input: `state.has_namespace("existing")` and `state.has_namespace("missing")`
    - Expected: True for existing, False for missing
    - Verification: Correct boolean values returned

## Session Model Tests

### State Field Integration
18. **Session with State**
    - Input: Create session with state data
    - Expected: State field properly stored
    - Verification: State accessible via session.state

19. **Session Serialization with State**
    - Input: Session with state data → to_dict() → from_dict()
    - Expected: State preserved through serialization
    - Verification: Deserialized state matches original

20. **Backward Compatibility**
    - Input: Session dict without state field
    - Expected: Session loads with empty state
    - Verification: No errors, state field defaults to empty dict

## SessionManager Tests

### Unified Persistence
21. **Update Session Method**
    - Input: Agent with message and state changes
    - Expected: Both message and state persisted together
    - Verification: Session contains both message and current state

22. **State Restoration**
    - Input: Agent initialized with session manager
    - Expected: Agent state restored from session
    - Verification: Agent state matches saved session state

## Integration Tests

### End-to-End Persistence
23. **Agent State Persistence Cycle**
    - Input: Create agent, modify state, save session, create new agent
    - Expected: New agent has same state as original
    - Verification: State values match across agent instances

24. **Multiple Namespace Persistence**
    - Input: Agent with state in multiple namespaces
    - Expected: All namespaces persisted and restored
    - Verification: All namespace data preserved

### Error Handling
25. **Persistence Failure Handling**
    - Input: Session manager that fails to save
    - Expected: Error logged, agent continues functioning
    - Verification: Agent remains operational despite persistence failure

26. **State Validation Error Handling**
    - Input: Attempt to set non-serializable value
    - Expected: Clear error message, state unchanged
    - Verification: Previous state values remain intact

## SDK Integration Tests

### Callback Handler Integration
27. **State Change Triggers Persistence**
    - Input: Agent with session manager, state modification
    - Expected: State change triggers callback handler
    - Verification: Session updated with new state

28. **SDK Namespace Population**
    - Input: Agent with conversation manager
    - Expected: SDK metadata stored in "sdk" namespace
    - Verification: SDK namespace contains expected metadata

## Performance Tests

### Large State Handling
29. **Large State Serialization**
    - Input: State with large amounts of data
    - Expected: Serialization completes without errors
    - Verification: Performance within acceptable limits

30. **Concurrent State Access**
    - Input: Multiple threads accessing state simultaneously
    - Expected: No data corruption or race conditions
    - Verification: State integrity maintained
