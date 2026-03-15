# Use Case Diagram — CadArena

## الغرض
يعرض حالات الاستخدام الأساسية للزوار والمستخدمين المسجلين والخدمات الخارجية.

## المخطط
```mermaid
flowchart TD
    Guest(["👤 زائر"])
    User(["👤 مستخدم مسجّل"])
    LLM(["⚙️ مزود LLM\nOllama / HF"])
    SMTP(["📧 SMTP"])
    FS(["🗂️ نظام الملفات"])

    subgraph CadArena ["نظام CadArena"]
        UC_CREATE_LOCAL["إنشاء مشروع محلي"]
        UC_AUTH["تسجيل / دخول"]
        UC_MANAGE["إدارة المشاريع"]
        UC_PROFILE["إدارة الملف الشخصي"]
        UC_KEYS["إدارة مفاتيح المزودات"]
        UC_CONTACT["إرسال رسالة تواصل"]

        subgraph GEN ["توليد DXF"]
            UC_GEN_DXF["إرسال وصف لتوليد DXF"]
            UC_PARSE["تحليل الوصف"]
            UC_LAYOUT["توليد مخطط ومساحات"]
            UC_DXF["توليد DXF"]
            UC_GEN_DXF -->|include| UC_PARSE
            UC_PARSE -->|include| UC_LAYOUT
            UC_LAYOUT -->|include| UC_DXF
        end

        subgraph EXPORT ["التصدير"]
            UC_EXPORT["تحميل / تصدير DXF"]
            UC_UPLOAD["رفع ملف DXF"]
            UC_READ["قراءة ملفات الإخراج"]
            UC_EXPORT -->|include| UC_READ
        end
    end

    Guest --> UC_CREATE_LOCAL
    Guest --> UC_GEN_DXF
    Guest --> UC_EXPORT
    Guest --> UC_UPLOAD
    Guest --> UC_CONTACT

    User --> UC_AUTH
    User --> UC_MANAGE
    User --> UC_PROFILE
    User --> UC_KEYS
    User --> UC_GEN_DXF
    User --> UC_EXPORT
    User --> UC_CONTACT

    LLM -.->|يُستدعى من| UC_PARSE
    SMTP -.->|يُستدعى من| UC_CONTACT
    FS -.->|يُستدعى من| UC_READ
```

## ملاحظات معمارية
- مسار الزائر يعتمد على `user_id` محلي في المتصفح، بينما مسار المسجّل يعتمد على JWT عبر `/auth/me`.
- التحليل يستدعي مزودات خارجية (Ollama/HF)، لكن التخطيط والرسم يتمان محلياً داخل `domain/`.
- تصدير DXF/PNG/PDF يتطلب الوصول إلى `backend/output/` وفق `resolve_output_path`.