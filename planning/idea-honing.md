# Idea Honing: Requirements Clarification

This document captures the interactive requirements clarification process for the persistence feature.

## Question 1: Persistence Scope and Triggers

**Question:** When should the persistence system save state? Should it save continuously during agent execution, only at specific checkpoints (like before/after tool calls), or triggered by specific events? Also, what should trigger a restore operation - only manual restarts, or should it also handle automatic recovery from crashes?

**Answer:** State should be saved through the callback_handler. There are specific lifecycle events that should be saved at.

## Question 2: Specific Lifecycle Events

**Question:** Which specific lifecycle events in the callback_handler should trigger state persistence? For example, should we save state on events like `on_agent_start`, `on_tool_call_start`, `on_tool_call_end`, `on_message_received`, `on_response_generated`, or other specific callback events? What's the most critical timing for ensuring we can recover properly?

**Answer:** Save on every message, so when the agent is invoked, "on_message_received", and on the agent response.

## Question 3: Storage Backend and Format

**Question:** Where and how should the persistence data be stored? Should it use local files (JSON, SQLite, pickle), a database (PostgreSQL, Redis), cloud storage, or should it be configurable to support multiple backends? Also, what format would be most appropriate for serializing the agent state, messages, and customer data?

**Answer:** I want to create an interface for storing different persistence data in different backends. The interface should be agnostic. To start, a file based storage is fine like in the recent git commit.

## Question 4: State Data Structure and Scope

**Question:** You mentioned three types of state: agent state, customer state, and request state. Can you clarify what specific data should be included in each? For example:
- Agent state: conversation history, current tools, model configuration, etc.?
- Customer state: user preferences, session data, authentication info?
- Request state: current request being processed, intermediate results, tool call progress?

What are the key pieces of data for each state type that are critical for recovery?

**Answer:** 
1. For agent state: lets only store the conversation history for now.
2. For customer state, this should be a python dictionary. Basically a json serializable object
3. Request state should store the current state of the event_loop between the current AgentResponse; so the latest agent message, event_loop_metrics, and the stop_reason

## Question 5: Session and Recovery Identification

**Question:** How should the system identify and manage different agent sessions or conversations for persistence? Should each agent instance have a unique session ID, or should it be based on customer/user identification? When an agent restarts, how should it determine which persisted state to restore - should it be automatic based on some identifier, or should the user/application specify which session to restore?

**Answer:** Unique identifiers should be defined outside of the generic interface. But you can identify a request by a unique session_id + a agent_id + a user_id.

## Question 6: Error Handling and Recovery Strategy

**Question:** What should happen if the persistence system encounters errors during save or restore operations? Should it fail silently, log warnings, or raise exceptions? Also, if corrupted or incomplete state data is found during recovery, should the system start fresh, attempt partial recovery, or provide options to the user? How should version compatibility be handled if the agent's data structures change over time?

**Answer:** The save system should throw an exception if it is not able to save the response. During recovery, if corrupted or incomplete data is found, then an error should be thrown.

## Question 7: Integration with Existing Agent Architecture

**Question:** How should the persistence feature integrate with the existing Strands Agent architecture? Should it be an optional component that can be enabled/disabled, or should it be built into the core agent? Should the persistence be configured when creating an Agent instance, or should it be a separate service that the agent connects to? Also, should the existing callback_handler interface be extended, or should persistence be implemented as a specific type of callback handler?

**Answer:** Lets build it into the core agent. It will be a new attribute on the Agent class, that is passed in during initialization. Under the hood, this will be implemented as a callback_handler on the agent. Look at the current file based implementation for how this will work.

## Question 8: Configuration and Customization

**Question:** What configuration options should be available for the persistence system? For example, should users be able to configure:
- Which types of state to persist (agent/customer/request - or all by default)?
- How frequently to save state (every message, or configurable intervals)?
- Storage location/path for file-based storage?
- Maximum storage size or cleanup policies for old sessions?
- Whether to automatically restore state on agent initialization or require explicit restore calls?

**Answer:** 
1. The messages, request state, and the customer state should all be persisted by default.
2. Always persist every message
3. By default, use a temp dir for storage, but allow for this to be customized
4. No max storage size
5. Automatically restore state if the persistence impl is passed in during initialization

## Question 9: API Design and Usage Pattern

**Question:** How should developers interact with the persistence feature? Should there be explicit methods to:
- Save/load customer state programmatically?
- Clear or reset persisted data?
- Query what sessions exist for a given user/agent combination?
- Export/import session data?

Also, what should the typical usage pattern look like when creating an agent with persistence enabled?

**Answer:** The persistence is a class initialized and passed into the agent class. This can be a new input parameter to the Agent class. This should have typical CRUD methods.

## Question 10: Threading and Concurrency

**Question:** Should the persistence system handle concurrent access scenarios? For example, if multiple agent instances are running simultaneously with the same session identifiers, or if the same agent is processing multiple requests concurrently, how should the persistence system handle potential race conditions or data conflicts? Should it include locking mechanisms, or is this outside the scope for the initial implementation?

**Answer:** No, there should only be one instance of an agent running at one time.

## Requirements Summary
