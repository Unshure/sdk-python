# Repository Paths Mapping

## Implementation Files

### New Files to Create
- **AgentState Class**: `src/strands/agent/state.py`
- **AgentState Tests**: `tests/agent/test_agent_state.py`

### Files to Modify
- **Session Model**: `src/strands/session/models.py`
  - Add `state: Dict[str, Any] = field(default_factory=dict)` to Session dataclass
  - Update `to_dict()` and `from_dict()` methods to handle state field
  
- **SessionManager Interface**: `src/strands/session/session_manager.py`
  - Rename `save_message()` to `update_session()`
  - Update method signatures and documentation
  
- **Default SessionManager**: `src/strands/session/default_session_manager.py`
  - Implement renamed `update_session()` method
  - Add state persistence logic
  
- **Agent Class**: `src/strands/agent/agent.py`
  - Add `self.state = AgentState()` in `__init__`
  - Update callback handler to trigger on state changes
  - Enhance session restoration to include state

### Test Files to Create/Modify
- **AgentState Unit Tests**: `tests/agent/test_agent_state.py`
- **Session Model Tests**: `tests/session/test_models.py` (if exists, modify; otherwise create)
- **SessionManager Tests**: `tests/session/test_session_manager.py` (if exists, modify)
- **Integration Tests**: `tests/integration/test_agent_state_persistence.py`

## Documentation Files

### Planning Documentation (Current Directory)
- **Code Context**: `agent_state_exploration/implementation/agent-state-enhancement/context/code_context.md`
- **Repository Paths**: `agent_state_exploration/implementation/agent-state-enhancement/context/repo_paths.md`
- **Test Scenarios**: `agent_state_exploration/implementation/agent-state-enhancement/plan/test_scenarios.md`
- **Implementation Plan**: `agent_state_exploration/implementation/agent-state-enhancement/plan/implementation_plan.md`
- **TDD Cycles**: `agent_state_exploration/implementation/agent-state-enhancement/documentation/tdd_cycles.md`
- **Test Plan**: `agent_state_exploration/implementation/agent-state-enhancement/documentation/test_plan.md`
- **Commit Status**: `agent_state_exploration/implementation/agent-state-enhancement/documentation/commit_status.md`

## Directory Structure

```
/workplace/ncclegg/sdk-python/
├── src/strands/
│   ├── agent/
│   │   ├── agent.py (modify)
│   │   └── state.py (create)
│   └── session/
│       ├── models.py (modify)
│       ├── session_manager.py (modify)
│       └── default_session_manager.py (modify)
├── tests/
│   ├── agent/
│   │   └── test_agent_state.py (create)
│   ├── session/
│   │   ├── test_models.py (create/modify)
│   │   └── test_session_manager.py (create/modify)
│   └── integration/
│       └── test_agent_state_persistence.py (create)
└── agent_state_exploration/
    └── implementation/
        └── agent-state-enhancement/
            ├── context/
            ├── plan/
            └── documentation/
```
