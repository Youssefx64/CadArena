# 02_state_machine_diagram (حالات طلب توليد DXF في workspace) — CadArena

## الغرض
يصف هذا المخطط حالات معالجة طلب توليد DXF في مسار workspace بما في ذلك إعادة المحاولة في حال فشل التخطيط الحتمي.

## المخطط

```mermaid
stateDiagram-v2
    state "خامل" as IDLE_STATE
    state "حفظ رسالة المستخدم" as PERSIST_USER_MSG
    state "تحليل الوصف" as PARSING_STATE
    state "إعادة المحاولة اللينة" as SOFT_RETRY_STATE
    state "إعادة المحاولة الصارمة" as HARD_RETRY_STATE
    state "بناء Intent" as BUILD_INTENT_STATE
    state "توليد DXF" as GENERATING_STATE
    state "حفظ رسالة المساعد" as PERSIST_ASSIST_MSG
    state "مكتمل" as COMPLETED_STATE
    state "فشل" as FAILED_STATE

    [*] --> IDLE_STATE
    IDLE_STATE --> PERSIST_USER_MSG : "POST /workspace/.../generate-dxf"
    PERSIST_USER_MSG --> PARSING_STATE

    PARSING_STATE --> SOFT_RETRY_STATE : "LAYOUT_* قابل لإعادة المحاولة"
    SOFT_RETRY_STATE --> PARSING_STATE : "إعادة المحاولة (Feasibility override)"
    SOFT_RETRY_STATE --> HARD_RETRY_STATE : "فشل المحاولة اللينة"
    HARD_RETRY_STATE --> PARSING_STATE : "إعادة المحاولة (Emergency fallback)"

    PARSING_STATE --> BUILD_INTENT_STATE : "نجاح التحليل"
    PARSING_STATE --> FAILED_STATE : "خطأ غير قابل لإعادة المحاولة"

    BUILD_INTENT_STATE --> GENERATING_STATE : "DesignIntent.model_validate"
    BUILD_INTENT_STATE --> FAILED_STATE : "DXF_INTENT_INVALID"

    GENERATING_STATE --> PERSIST_ASSIST_MSG : "generate_dxf_from_intent"
    GENERATING_STATE --> FAILED_STATE : "GENERATE_DXF_FAILED"

    PERSIST_ASSIST_MSG --> COMPLETED_STATE

    COMPLETED_STATE --> [*]
    FAILED_STATE --> [*]
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- إعادة المحاولة في workspace تُفعّل فقط لأخطاء التخطيط المحددة في `_LAYOUT_RETRY_CODES` داخل `workspace.py`.
- التحويل إلى `DesignIntent` يتم بعد نجاح التحليل وقبل استدعاء خط DXF لضمان صلاحية النموذج.
- إضافة الرسائل إلى قاعدة البيانات تتم عند البداية والنهاية لتوثيق الحوار حتى في حالات الفشل.
