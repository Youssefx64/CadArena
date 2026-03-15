# 07_timing_diagram (توقيت مراحل التوليد في الطلب الواحد) — CadArena

## الغرض
يوضح هذا المخطط توقيت المراحل الرئيسة لمعالجة طلب توليد DXF من لحظة الإرسال حتى حفظ الملف والاستجابة.

## المخطط

```mermaid
timeline
    title "توقيت معالجة طلب توليد DXF"
    section Frontend
      T0: "إدخال الوصف"
      T1: "إرسال POST إلى /workspace/.../generate-dxf"
    section Backend
      T2: "add_message(user) في workspace_storage"
      T3: "PromptCompiler + Provider.generate"
      T4: "OutputParser + ExtractedIntentValidator"
      T5: "DeterministicLayoutPlanner + OpeningPlanner"
      T6: "IntentValidator + LayoutValidator (metrics)"
      T7: "DesignIntent.model_validate"
      T8: "generate_dxf_from_intent"
      T9: "DXFRoomRenderer.save"
    section Storage
      T10: "حفظ DXF في backend/output/dxf"
      T11: "add_message(assistant) وتحديث المشروع"
    section Frontend
      T12: "استلام الاستجابة وعرض رابط المعاينة"
```
<!-- VALIDATED: no <<>> inline, no Arabic outside quotes, no reserved keywords as IDs -->

## ملاحظات معمارية
- خطوات التحليل والتخطيط تسبق توليد DXF ولا تُنفذ بالتوازي لضمان صحة الهندسة.
- التوقيت الفعلي يعتمد على مزود LLM وحجم البرنامج، لكن ترتيب المراحل ثابت كما في التسلسل أعلاه.
- حفظ الملف يأتي قبل تحديث رسالة المساعد لضمان أن رابط `dxf_path` يشير إلى ملف موجود.
