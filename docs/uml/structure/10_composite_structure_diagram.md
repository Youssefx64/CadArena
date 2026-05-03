# 10 Composite Structure Diagram - DesignParseOrchestrator Internals - CadArena

## Purpose
This composite structure diagram shows the internal parts of `DesignParseOrchestrator` and the order in which those parts collaborate to produce a validated layout.

## Diagram

```mermaid
classDiagram
    class DesignParseOrchestrator {
        -_prompt_compiler: PromptCompiler
        -_output_parser: OutputParser
        -_extracted_intent_validator: ExtractedIntentValidator
        -_prompt_program_deriver: PromptProgramDeriver
        -_layout_planner: DeterministicLayoutPlanner
        -_opening_planner: DeterministicOpeningPlanner
        -_layout_validator: LayoutValidator
        -_intent_validator: IntentValidator
        -_providers: dict
        +startup()
        +shutdown()
        +parse(prompt, model_choice, recovery_mode, request_id)
    }

    class PromptNormalizer {
        +normalize_arabic_prompt()
        +extract_expected_room_counts()
    }
    class PromptCompiler {
        +compile(user_prompt)
    }
    class ProviderMap {
        +ollama
        +huggingface
        +qwen_cloud
    }
    class LLMProviderPort {
        <<interface>>
        +generate(compiled_prompt, request_id)
    }
    class OllamaProviderClient
    class QwenCloudProviderClient
    class HuggingFaceProviderClient
    class OutputParser {
        +parse(raw_output)
    }
    class JsonRepair {
        +extract_permissive_json()
        +build_repair_prompt()
        +build_prompt_fallback()
    }
    class SelfReview {
        +review_extracted_payload()
        +correct_room_counts()
        +apply_furniture_hints()
    }
    class ExtractedIntentValidator {
        +validate(extracted_payload)
    }
    class PromptProgramDeriver {
        +derive(prompt, extracted_payload)
    }
    class DeterministicLayoutPlanner {
        +plan_with_metadata(extracted_payload)
    }
    class DeterministicOpeningPlanner {
        +plan(extracted_payload, layout_payload)
    }
    class IntentValidator {
        +validate(planned_payload)
    }
    class LayoutValidator {
        +validate(planned_payload)
        +return_layout_metrics()
    }
    class EmergencyFallback {
        +build_fallback_room_program()
        +build_emergency_grid_layout()
        +build_emergency_metrics()
    }
    class ParseOrchestrationResult {
        +model_used
        +provider_used
        +failover_triggered
        +self_review_triggered
        +data
        +metrics
    }

    DesignParseOrchestrator *-- PromptCompiler
    DesignParseOrchestrator *-- OutputParser
    DesignParseOrchestrator *-- ExtractedIntentValidator
    DesignParseOrchestrator *-- PromptProgramDeriver
    DesignParseOrchestrator *-- DeterministicLayoutPlanner
    DesignParseOrchestrator *-- DeterministicOpeningPlanner
    DesignParseOrchestrator *-- IntentValidator
    DesignParseOrchestrator *-- LayoutValidator
    DesignParseOrchestrator *-- ProviderMap

    ProviderMap o-- LLMProviderPort
    OllamaProviderClient ..|> LLMProviderPort
    QwenCloudProviderClient ..|> LLMProviderPort
    HuggingFaceProviderClient ..|> LLMProviderPort

    DesignParseOrchestrator ..> PromptNormalizer
    DesignParseOrchestrator ..> JsonRepair
    DesignParseOrchestrator ..> SelfReview
    DesignParseOrchestrator ..> EmergencyFallback
    DesignParseOrchestrator ..> ParseOrchestrationResult

    PromptNormalizer --> PromptCompiler
    PromptCompiler --> ProviderMap
    ProviderMap --> OutputParser
    OutputParser --> JsonRepair
    JsonRepair --> SelfReview
    SelfReview --> ExtractedIntentValidator
    ExtractedIntentValidator --> PromptProgramDeriver
    PromptProgramDeriver --> DeterministicLayoutPlanner
    DeterministicLayoutPlanner --> DeterministicOpeningPlanner
    DeterministicOpeningPlanner --> IntentValidator
    IntentValidator --> LayoutValidator
    LayoutValidator --> ParseOrchestrationResult
    EmergencyFallback --> ParseOrchestrationResult
```

## Architectural Notes
- The orchestrator owns long-lived component instances and coordinates them in a fixed pipeline.
- Provider selection is request-scoped for model overrides, while the stable provider map remains inside the singleton parser service.
- JSON repair, self-review, quality correction, and emergency fallback are internal recovery responsibilities rather than separate routers.
- The final result includes both validated geometry and layout metrics so callers can render or explain the generated plan.
