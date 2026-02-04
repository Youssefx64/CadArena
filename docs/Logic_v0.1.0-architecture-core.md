# Backend Logic (CadArena)

> هذا الملف يشرح منطق الـ backend كما هو منفّذ حاليًا في الكود.

## نظرة عامة
الـ backend يوفر واجهتين API أساسيتين لتوليد ملفات DXF:
1) `/api/v1/draw/rectangle` يرسم مستطيل بسيط.
2) `/api/v1/generate-dxf` يبني مخطط غرف كامل انطلاقًا من Design Intent.

المعمارية تعتمد على خطّين (pipelines):
- **draw_rectangle_pipeline**: يتحقق من صحة الأبعاد، يحوّل المستطيل لنقاط، ويرسمه إلى DXF.
- **generate_dxf_from_intent**: ينفّذ سلسلة خطوات تخطيط غرف + توليد جدران + أبواب + قطع الجدران + رسم DXF.

## طبقة الـ API
الملفات الأساسية:
- `backend/app/main.py`: يجهّز FastAPI ويضيف router.
- `backend/app/api/v1/routes.py`: يعرّف نقطتي النهاية.

**تدفق الطلبات:**
- `/draw/rectangle` يستقبل `RectangleGeometry` → يمرّ على `draw_rectangle_pipeline` → يرجع مسار ملف DXF.
- `/generate-dxf` يستقبل `DesignIntent` → يمرّ على `generate_dxf_from_intent` → يرجع مسار ملف DXF النهائي.

## الـ Schemas (المدخلات والكيانات)
- `DesignIntent`: يحتوي boundary + rooms + openings.
- `RoomIntent`: اسم الغرفة، نوعها، أبعادها.
- `OpeningIntent`: نوع الفتحة (door/window)، عرضها، الحائط المستهدف، والإزاحة.
- `RectangleGeometry` و `Point` لتعريف الإحداثيات.
- `Room`: كيان غرفة فعلي بعد وضعها على المخطط.

## Pipeline: draw_rectangle_pipeline
الملف: `backend/app/pipeline/draw_pipeline.py`

الخطوات:
1) التحقق من صحة الأبعاد عبر `validate_rectangle`:
   - العرض والارتفاع > 0.
   - الحد الأدنى 2 متر لكل بُعد.
2) تحويل المستطيل إلى 4 نقاط عبر `rectangle_to_points`.
3) إنشاء اسم ملف DXF بختم زمني عبر `generate_dxf_filename`.
4) رسم المستطيل في DXF عبر `draw_rectangle`.

## Pipeline: generate_dxf_from_intent
الملف: `backend/app/pipeline/intent_to_agent.py`

### الخطوة 1: بناء الـ Boundary
- يتم تحويل `BoundaryIntent` إلى `RectangleGeometry` بأصل (0,0).

### الخطوة 2: إنشاء PlannerAgent
- الـ agent هو المسؤول عن وضع الغرف داخل الحدود مع احترام القيود.

### الخطوة 3: وضع الغرف
- لكل غرفة في `intent.rooms`:
  - يتم تحويلها إلى `Room`.
  - استدعاء `PlannerAgent.place_room` لمحاولة إيجاد موضع مناسب.

### الخطوة 4: توليد الجدران وتحديد الأبواب
- لكل غرفة موضوعة:
  - توليد 4 جدران عبر `generate_wall_segments` (bottom, right, top, left).
  - تسجيل الجدران في `WallCutManager`.
  - تحديد الباب:
    - إذا كان هناك `OpeningIntent` للباب: يُستخدم `place_door_on_wall` وفق الحائط والإزاحة.
    - وإلا: `auto_place_door_on_room` يضع الباب في منتصف الحائط السفلي.
  - تسجيل الباب في `WallCutManager`.

### الخطوة 5: قطع الجدران عند موضع الأبواب
- `WallCutManager.process_cuts` يُقسّم كل جدار إلى قطع قبل/بعد فتحة الباب.
- الناتج: `final_wall_segments` بدون أجزاء الباب.

### الخطوة 5b: قطع حدود المبنى (Boundary)
- يتم توليد جدران الحدود عبر `generate_boundary_segments`.
- `WallCutManager` آخر يقطع حدود المبنى لو كان الباب ملاصقًا للحد الخارجي.
- يعتمد على حساب تطابق فتحات الأبواب مع الجدار الخارجي.

### الخطوة 6: حساب هندسة الباب
- `compute_door_geometry` ينتج:
  - نقطة المفصلة.
  - نهاية الضلفة.
  - نصف قطر القوس.
  - زوايا الفتح والإغلاق.

### الخطوة 7: الرسم في DXF
- `DXFRoomRenderer` يرسم:
  - حدود المبنى.
  - الجدران بعد القطع.
  - تمثيل الأبواب (خط الضلفة + قوس الفتح).
  - تسميات الغرف وأبعادها.

### الخطوة 8: الحفظ
- يتم حفظ الملف في `output/` باسم يبدأ بـ `layout_` ويحتوي على timestamp.

## منطق الـ PlannerAgent
الملف: `backend/app/domain/planner/planner_agent.py`

**الهدف:** إيجاد موضع لكل غرفة داخل حدود المبنى بدون تداخل ومع مسافات فاصلة.

**آلية العمل:**
- يستخدم استراتيجية Grid بسيطة بعرض خطوة 1 متر.
- يجرب حتى `PlannerConfig.MAX_PLACEMENT_TRIES` (الافتراضي 100 محاولة).
- لكل محاولة:
  1) يقترح origin عبر `_propose_position`.
  2) يطبق 3 قيود:
     - `BoundaryConstraint`: الغرفة بالكامل داخل الحدود.
     - `OverlapConstraint`: لا يوجد تداخل مع الغرف الأخرى.
     - `SpacingConstraint`: يوجد حد أدنى للمسافة (افتراضي 0.5م).

إذا نجحت القيود، تُعتمد الغرفة وتُضاف للقائمة.

## القيود (Constraints)
- **BoundaryConstraint**: يتحقق من أن المستطيل بالكامل ضمن boundary.
- **OverlapConstraint**: يمنع تداخل مساحات الغرف.
- **SpacingConstraint**: يضمن فراغًا أدنى بين الغرف (إما أفقيًا أو عموديًا).

## منطق الجدران والأبواب
- `generate_wall_segments`: يحوّل كل غرفة إلى 4 جدران محورية.
- `place_door_on_wall`: يضع الباب على جدار محدد، ويتحقق أن العرض مناسب.
- `auto_place_door_on_room`: يضع الباب تلقائيًا في منتصف الجدار السفلي.
- `WallCutManager`: يقص الجدار في موضع الباب، مع دمج الفتحات المتداخلة.
- `compute_door_geometry`: يحسب اتجاه الضلفة وقوس الفتح بناءً على المفصلة واتجاه الدوران.

## DXF Rendering
الملف: `backend/app/services/dxf_room_renderer.py`

**الطبقات (Layers):**
- BOUNDARY, WALLS, DOORS, WINDOWS, ROOM_TEXT, DIMENSIONS, STAIRS.

**الرسم:**
- الجدران والحدود تُرسم كخطين متوازيين بسمك ثابت.
- الباب يُرسم كخط للضلفة + قوس لحركة الفتح.
- النصوص تُستخدم لتسمية الغرف وإظهار الأبعاد.

## ملاحظات مهمة
- الملفات في `domain/openings/` و `schemas/opening.py` موجودة لكنها ليست ضمن مسار `generate_dxf_from_intent` الحالي.
- تخطيط الغرف بسيط (Grid) وليس Optimization متقدم.
- توليد النوافذ موجود كـ helpers لكنه غير مستخدم في الـ pipeline الحالي.

## المخرجات
- ملفات DXF تحفظ في مجلد `backend/output` باسم مثل:
  - `layout_YYYYMMDD_HHMMSS.dxf`
  - `rectangle_WxH_YYYYMMDD_HHMMSS.dxf`
