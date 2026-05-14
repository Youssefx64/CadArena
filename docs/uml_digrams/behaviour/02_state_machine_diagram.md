# 02 State Machine Diagram - Workspace Design Request Lifecycle - CadArena

## Purpose
This state machine describes how a workspace design request moves through conversational routing, full generation, iterative editing, retry handling, DXF rendering, persistence, and failure reporting.

## Diagram

```mermaid
stateDiagram-v2
    state "Idle" as IDLE_STATE
    state "Resolve workspace scope" as RESOLVE_SCOPE_STATE
    state "Load project" as LOAD_PROJECT_STATE
    state "Persist user message" as PERSIST_USER_STATE
    state "Classify prompt intent" as CLASSIFY_INTENT_STATE
    state "Conversation reply" as CONVERSATION_STATE
    state "Choose design mode" as CHOOSE_MODE_STATE
    state "Full parse" as FULL_PARSE_STATE
    state "Soft layout retry" as SOFT_RETRY_STATE
    state "Hard layout retry" as HARD_RETRY_STATE
    state "Iterative patch" as ITERATIVE_PATCH_STATE
    state "Build DXF intent" as BUILD_INTENT_STATE
    state "Generate DXF" as GENERATE_DXF_STATE
    state "Issue file token" as ISSUE_TOKEN_STATE
    state "Persist assistant message" as PERSIST_ASSISTANT_STATE
    state "Return success" as SUCCESS_STATE
    state "Persist error message" as PERSIST_ERROR_STATE
    state "Return failure" as FAILURE_STATE

    [*] --> IDLE_STATE
    IDLE_STATE --> RESOLVE_SCOPE_STATE : "POST workspace request"
    RESOLVE_SCOPE_STATE --> LOAD_PROJECT_STATE : "guest user_id or JWT user"
    LOAD_PROJECT_STATE --> PERSIST_USER_STATE : "project found"
    LOAD_PROJECT_STATE --> FAILURE_STATE : "PROJECT_NOT_FOUND"
    PERSIST_USER_STATE --> CLASSIFY_INTENT_STATE

    CLASSIFY_INTENT_STATE --> CONVERSATION_STATE : "MessageIntent.CONVERSATION"
    CONVERSATION_STATE --> PERSIST_ASSISTANT_STATE : "chat_assistant reply"

    CLASSIFY_INTENT_STATE --> CHOOSE_MODE_STATE : "design request"
    CHOOSE_MODE_STATE --> FULL_PARSE_STATE : "no current layout"
    CHOOSE_MODE_STATE --> ITERATIVE_PATCH_STATE : "current_layout exists"

    FULL_PARSE_STATE --> SOFT_RETRY_STATE : "retryable LAYOUT_* or invalid structured output"
    SOFT_RETRY_STATE --> FULL_PARSE_STATE : "feasibility override prompt"
    SOFT_RETRY_STATE --> HARD_RETRY_STATE : "soft retry failed"
    HARD_RETRY_STATE --> FULL_PARSE_STATE : "emergency fallback prompt"

    FULL_PARSE_STATE --> BUILD_INTENT_STATE : "ParsedDesignIntent returned"
    ITERATIVE_PATCH_STATE --> BUILD_INTENT_STATE : "updated layout returned"

    BUILD_INTENT_STATE --> GENERATE_DXF_STATE : "DesignIntent.model_validate"
    BUILD_INTENT_STATE --> PERSIST_ERROR_STATE : "DXF_INTENT_INVALID"

    GENERATE_DXF_STATE --> ISSUE_TOKEN_STATE : "renderer saved DXF"
    GENERATE_DXF_STATE --> PERSIST_ERROR_STATE : "GENERATE_DXF_FAILED"

    ISSUE_TOKEN_STATE --> PERSIST_ASSISTANT_STATE : "file_token or preview_token"
    PERSIST_ASSISTANT_STATE --> SUCCESS_STATE
    PERSIST_ERROR_STATE --> FAILURE_STATE

    SUCCESS_STATE --> [*]
    FAILURE_STATE --> [*]
```

## Architectural Notes
- Guest workspace routes receive a `user_id`; authenticated workspace routes derive the user from the JWT cookie and reuse the shared generation function.
- Full generation persists user and assistant messages, while iterative routes return an updated layout and may issue a preview token without exposing a raw path.
- Retry states are limited to layout and structured-output failures that can reasonably be corrected by prompt relaxation or emergency fallback.
- Every terminal path returns a structured payload that the Studio can render as either chat, layout, preview, or error feedback.
