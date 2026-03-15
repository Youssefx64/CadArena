# 14_profile_diagram (بروفايل الستيريотипات لطبقات النظام) — CadArena

## الغرض
يعرض هذا المخطط البروفايل المعماري المستخدم لتصنيف العناصر داخل CadArena عبر ستيريотипات واضحة (Router/Service/Domain/Storage/Port/Adapter/External).

## المخطط

```mermaid
classDiagram
    class WorkspaceRouter {
        <<Router>>
    }
    class DesignParserRouter {
        <<Router>>
    }
    class AuthRouter {
        <<Router>>
    }

    class DesignParseOrchestrator {
        <<Service>>
    }
    class LayoutValidator {
        <<Service>>
    }
    class ContactEmailService {
        <<Service>>
    }

    class PlannerAgent {
        <<Domain>>
    }
    class WallCutManager {
        <<Domain>>
    }
    class DoorSpec {
        <<Domain>>
    }

    class AuthStorage {
        <<Storage>>
    }
    class WorkspaceStorage {
        <<Storage>>
    }

    class LLMProviderPort {
        <<Port>>
    }
    class DXFGeneratorPort {
        <<Port>>
    }

    class PipelineDXFGenerator {
        <<Adapter>>
    }

    class OllamaProviderClient {
        <<External>>
    }
    class HuggingFaceProviderClient {
        <<External>>
    }
    class SMTPServer {
        <<External>>
    }

    WorkspaceRouter ..> DesignParseOrchestrator : "يستخدم"
    WorkspaceRouter ..> WorkspaceStorage : "يكتب/يقرأ"
    DesignParserRouter ..> DesignParseOrchestrator : "يستخدم"
    AuthRouter ..> AuthStorage : "يكتب/يقرأ"

    DesignParseOrchestrator ..> LLMProviderPort : "يعتمد"
    OllamaProviderClient ..|> LLMProviderPort
    HuggingFaceProviderClient ..|> LLMProviderPort

    PipelineDXFGenerator ..|> DXFGeneratorPort

    DesignParseOrchestrator ..> LayoutValidator : "يتحقق"
    DesignParseOrchestrator ..> PlannerAgent : "يخطط"

    ContactEmailService ..> SMTPServer : "يرسل"
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- الستيريотипات تعكس الطبقات الفعلية في الشيفرة: routers كطبقة نقل، services كتنسيق، domain كمنطق هندسي، وstorage كطبقة SQLite/ملفات.
- اعتماد الخدمات على منافذ (Ports) يقلل الارتباط المباشر بالمزوّدات الخارجية ويتيح استبدالها.
- وجود Adapter مثل `PipelineDXFGenerator` يربط المنافذ بخط الرسم الحالي دون تغيير واجهات الاستخدام.
