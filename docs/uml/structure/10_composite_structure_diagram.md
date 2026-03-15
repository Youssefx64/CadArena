# 10_composite_structure_diagram (البنية الداخلية لـ DesignParseOrchestrator) — CadArena

## الغرض
يعرض هذا المخطط البنية الداخلية لمكوّن التحليل الحتمي DesignParseOrchestrator والعلاقات بين مكوناته الفرعية.

## المخطط

```mermaid
classDiagram
    class DesignParseOrchestrator {
        -_prompt_compiler
        -_output_parser
        -_extracted_intent_validator
        -_prompt_program_deriver
        -_layout_planner
        -_opening_planner
        -_layout_validator
        -_intent_validator
        -_providers
        +parse(prompt, model_choice, recovery_mode, request_id)
    }

    class PromptCompiler
    class OutputParser
    class ExtractedIntentValidator
    class PromptProgramDeriver
    class DeterministicLayoutPlanner
    class DeterministicOpeningPlanner
    class LayoutValidator
    class IntentValidator

    class LLMProviderPort {
        <<interface>>
        +generate(compiled_prompt, request_id)
    }
    class OllamaProviderClient
    class HuggingFaceProviderClient

    DesignParseOrchestrator *-- PromptCompiler
    DesignParseOrchestrator *-- OutputParser
    DesignParseOrchestrator *-- ExtractedIntentValidator
    DesignParseOrchestrator *-- PromptProgramDeriver
    DesignParseOrchestrator *-- DeterministicLayoutPlanner
    DesignParseOrchestrator *-- DeterministicOpeningPlanner
    DesignParseOrchestrator *-- LayoutValidator
    DesignParseOrchestrator *-- IntentValidator

    DesignParseOrchestrator ..> LLMProviderPort : "uses"
    OllamaProviderClient ..|> LLMProviderPort
    HuggingFaceProviderClient ..|> LLMProviderPort
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- المكوّن يستخدم تجميعاً صريحاً (composition) لعناصر التخطيط والتحقق لضمان ثبات سلسلة المعالجة.
- واجهة `LLMProviderPort` تسمح بتبديل المزود دون تغيير طبقات التخطيط أو التحقق.
- المزوّدات تُدار في قاموس داخلي مرتبط بقيمة `ParseDesignModel` مما يسهل التوسعة لاحقاً.
