# 02 State Machine Diagram - Workspace Design Request Lifecycle - CadArena

## Purpose
This state machine describes how a workspace request moves through authentication scope, routing, design generation, iterative editing, persistence, and failure handling.

## Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> ResolveScope: workspace request received
    ResolveScope --> LoadProject: guest id or authenticated user resolved
    LoadProject --> PersistUserMessage: project found
    LoadProject --> ReturnFailure: project not found

    PersistUserMessage --> ClassifyIntent
    ClassifyIntent --> ConversationReply: conversation intent
    ClassifyIntent --> SelectDesignMode: design intent

    ConversationReply --> PersistAssistantMessage

    SelectDesignMode --> FullParse: no current layout
    SelectDesignMode --> IterativePatch: current layout available

    FullParse --> CompilePrompt
    CompilePrompt --> ProviderGeneration
    ProviderGeneration --> ParseStructuredOutput
    ParseStructuredOutput --> RepairOutput: invalid output and repair enabled
    RepairOutput --> ParseStructuredOutput
    ParseStructuredOutput --> ValidateExtractedIntent: valid structured output
    ValidateExtractedIntent --> PlanLayout
    PlanLayout --> PlanOpenings
    PlanOpenings --> ValidateLayout

    ValidateLayout --> SoftRetry: retryable layout failure
    SoftRetry --> FullParse: relaxed feasibility prompt
    SoftRetry --> HardRetry: soft retry failed
    HardRetry --> FullParse: emergency fallback prompt

    ValidateLayout --> BuildDxfIntent: layout valid
    IterativePatch --> BuildDxfIntent: patch successful
    IterativePatch --> FullParse: full parse fallback required

    BuildDxfIntent --> GenerateDxf: intent valid
    BuildDxfIntent --> PersistErrorMessage: invalid intent
    GenerateDxf --> IssueFileToken: file saved
    GenerateDxf --> PersistErrorMessage: renderer failed

    IssueFileToken --> PersistAssistantMessage
    PersistAssistantMessage --> ReturnSuccess
    PersistErrorMessage --> ReturnFailure

    ReturnSuccess --> [*]
    ReturnFailure --> [*]
```

## Architectural Notes
- Guest workspace routes accept a `user_id`; authenticated routes derive user identity from the JWT cookie.
- Retry states are used only for layout and structured-output failures that can be corrected by a relaxed prompt.
- Terminal responses are structured so the frontend can render chat, layout, preview, or error feedback consistently.
