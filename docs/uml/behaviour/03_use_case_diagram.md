# Use Case Diagram — CadArena

## الغرض
يعرض حالات الاستخدام الأساسية للزوار والمستخدمين المسجلين والخدمات الخارجية.

## المخطط
```mermaid
flowchart TD
    Guest(["زائر"])
    User(["مستخدم مسجل"])
    LLM(["مزود LLM"])
    SMTP(["SMTP"])
    FS(["نظام الملفات"])

    subgraph CadArena["نظام CadArena"]
        UC_LOCAL["إنشاء مشروع محلي"]
        UC_AUTH["تسجيل / دخول"]
        UC_MANAGE["إدارة المشاريع"]
        UC_PROFILE["إدارة الملف الشخصي"]
        UC_KEYS["إدارة مفاتيح المزودات"]
        UC_CONTACT["إرسال رسالة تواصل"]
        UC_PARSE["تحليل الوصف"]
        UC_LAYOUT["توليد مخطط ومساحات"]
        UC_DXF["توليد DXF"]
        UC_UPLOAD["رفع ملف DXF"]
        UC_EXPORT["تصدير / تحميل DXF"]
        UC_READ["قراءة ملفات الإخراج"]
    end

    Guest --> UC_LOCAL
    Guest --> UC_PARSE
    Guest --> UC_UPLOAD
    Guest --> UC_EXPORT
    Guest --> UC_CONTACT

    User --> UC_AUTH
    User --> UC_MANAGE
    User --> UC_PROFILE
    User --> UC_KEYS
    User --> UC_PARSE
    User --> UC_UPLOAD
    User --> UC_EXPORT
    User --> UC_CONTACT

    UC_PARSE --> UC_LAYOUT
    UC_LAYOUT --> UC_DXF
    UC_EXPORT --> UC_READ

    LLM -.-> UC_PARSE
    SMTP -.-> UC_CONTACT
    FS -.-> UC_READ
```

## ملاحظات معمارية
- مسار الزائر يعتمد على `user_id` محلي، بينما المسجل يعتمد على JWT.
- التحليل يستدعي مزودات خارجية، لكن التخطيط والرسم محليان داخل النظام.
- رفع DXF والتصدير يعتمدان على ملفات `backend/output/`.