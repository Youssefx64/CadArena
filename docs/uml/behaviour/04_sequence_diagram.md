# 04 Sequence Diagram - Workspace DXF Generation - CadArena

## Purpose
This sequence diagram shows the detailed runtime interaction for generating a DXF from a new prompt inside the Studio workspace.

## Diagram

```mermaid
sequenceDiagram
    actor User
    participant ReactApp as React App
    participant Studio as Studio iframe
    participant WorkspaceRouter
    participant IntentRouter
    participant WorkspaceStorage
    participant ParserService
    participant Orchestrator
    participant Provider as LLM Provider
    participant OutputParser
    participant ExtractValidator
    participant LayoutPlanner
    participant OpeningPlanner
    participant IntentValidator
    participant LayoutValidator
    participant DXFPipeline
    participant FileTokenRegistry
    participant DXFRenderer
    participant FileSystem

    User->>ReactApp: Open /studio
    ReactApp->>Studio: Load /studio-app/index.html
    User->>Studio: Submit prompt and selected model
    Studio->>WorkspaceRouter: POST /api/v1/workspace/.../generate-dxf
    WorkspaceRouter->>WorkspaceStorage: get_project(user_id, project_id)
    WorkspaceRouter->>WorkspaceStorage: add_message(role=user)
    WorkspaceRouter->>IntentRouter: classify_intent(prompt)

    alt Conversational message
        WorkspaceRouter->>WorkspaceStorage: add_message(role=assistant)
        WorkspaceRouter-->>Studio: type=chat, message
    else Design generation
        WorkspaceRouter->>ParserService: parse_design_prompt_with_metadata(prompt, model, model_id, recovery_mode)
        ParserService->>Orchestrator: parse(...)
        Orchestrator->>Provider: generate(compiled_prompt)
        Provider-->>Orchestrator: raw_output
        Orchestrator->>OutputParser: parse(raw_output)

        alt Invalid JSON and repair enabled
            Orchestrator->>Provider: generate(JSON repair prompt)
            Provider-->>Orchestrator: repaired_output
            Orchestrator->>OutputParser: parse(repaired_output)
        end

        Orchestrator->>ExtractValidator: validate(extracted payload)
        Orchestrator->>Provider: optional self-review and correction
        Orchestrator->>LayoutPlanner: plan_with_metadata(extracted payload)
        Orchestrator->>OpeningPlanner: plan(layout payload)
        Orchestrator->>IntentValidator: validate(planned payload)
        Orchestrator->>LayoutValidator: validate(metrics)
        Orchestrator-->>ParserService: ParseOrchestrationResult
        ParserService-->>WorkspaceRouter: parsed data and metrics
        WorkspaceRouter->>DXFPipeline: run_in_threadpool(generate_dxf_from_intent)
        DXFPipeline->>DXFPipeline: DesignIntentValidator.validate
        DXFPipeline->>DXFPipeline: PlannerAgent places rooms
        DXFPipeline->>DXFPipeline: WallCutManager cuts openings
        DXFPipeline->>DXFRenderer: draw layers, walls, doors, windows, labels
        DXFRenderer->>FileSystem: save backend/output/dxf/*.dxf
        DXFPipeline-->>WorkspaceRouter: dxf_path
        WorkspaceRouter->>FileTokenRegistry: issue_workspace_file_token(user_id, dxf_path)
        FileTokenRegistry-->>WorkspaceRouter: file_token
        WorkspaceRouter->>WorkspaceStorage: add_message(role=assistant, file_token metadata)
        WorkspaceRouter-->>Studio: success payload with layout, metrics, suggestions, file_token
        Studio->>WorkspaceRouter: GET /api/v1/dxf/preview?file_token=...
        WorkspaceRouter->>FileSystem: resolve token and render preview
        WorkspaceRouter-->>Studio: PNG preview
    end

    alt Parser or DXF failure
        WorkspaceRouter->>WorkspaceStorage: add_message(role=error)
        WorkspaceRouter-->>Studio: ParseDesignErrorResponse
    end
```

## Architectural Notes
- The workspace router is the transaction coordinator for project lookup, chat persistence, parser invocation, DXF generation, token issuance, and response shaping.
- The parser returns both a strict `ParsedDesignIntent` and layout quality metrics; the router converts only the boundary, rooms, and openings into the DXF-facing `DesignIntent`.
- DXF generation runs in a threadpool so CPU-bound CAD rendering does not block the FastAPI event loop.
- The frontend preview request resolves a token back to a server file and then renders/export it through the DXF routes.
