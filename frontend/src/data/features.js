/**
 * central features registry database for CadArena.
 * DYNAMICALLY GENERATED from the codebase.
 * DO NOT EDIT MANUALLY.
 */

export const features = [
  {
    "id": "multi_turn_chat",
    "title": "Multi-Turn AI Chat",
    "category": "AI",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "AI",
      "Chat",
      "Workspace"
    ],
    "description": "Multi-turn assistant interface for structural, architectural and building code inquiries.",
    "fullDescription": "Provides a conversational layout workspace to interact with generative LLM engines. Integrates chat history, dynamic title generation, and robust server-side storage.",
    "workflows": [
      "User asks layout guidance question",
      "LLM processes query with context",
      "Response rendered in conversational thread"
    ],
    "dependencies": [
      "FastAPI Web Router",
      "SQLite DB Session"
    ]
  },
  {
    "id": "chat_history",
    "title": "Chat History & Persistence",
    "category": "Workspace",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "Workspace",
      "Data",
      "History"
    ],
    "description": "Persistent SQLite storage of user sessions, chat threads, and generated response objects.",
    "fullDescription": "Tracks all conversation threads, message content, and structured references. Features automated title generation using a lightweight summarizer based on the initial prompt.",
    "workflows": [
      "Save message context on send",
      "Load historical messages on select",
      "Delete thread",
      "Rename thread title"
    ],
    "dependencies": [
      "SQLite database",
      "SQLAlchemy ORM"
    ]
  },
  {
    "id": "rag_search",
    "title": "Retrieval-Augmented Generation",
    "category": "RAG",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "RAG",
      "Search",
      "Performance"
    ],
    "description": "Stand-alone vector retrieval engine querying local Qdrant collections for civil and architectural guidelines.",
    "fullDescription": "Injects verified regulatory standards directly into the LLM system prompt. Enables context-rich replies with minimal hallucination rates.",
    "workflows": [
      "Retrieve matching document chunks",
      "Calculate cosine similarity",
      "Inject context into prompt templates"
    ],
    "dependencies": [
      "Qdrant DB Store",
      "Embedding Providers (Cohere/OpenAI)"
    ]
  },
  {
    "id": "document_ingestion",
    "title": "Technical Document Ingestion",
    "category": "RAG",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "RAG",
      "Data",
      "Productivity"
    ],
    "description": "Multi-format file upload parser for PDF, TXT, Markdown, CSV, and JSON reference documents.",
    "fullDescription": "Handles raw text or file uploads. Automatically parses text, chunks content, computes embeddings, and updates the active Qdrant search indexing space.",
    "workflows": [
      "Upload reference file",
      "Extract text content",
      "Create index vector chunks"
    ],
    "dependencies": [
      "RAG API router",
      "Ollama/Cohere Embedding API"
    ]
  },
  {
    "id": "citations",
    "title": "Interactive Citations & Deep Links",
    "category": "Productivity",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "RAG",
      "Visualization",
      "Productivity"
    ],
    "description": "Clickable citations in AI answers linking to exact reference pages or coordinates in the workspace.",
    "fullDescription": "Ties generative responses to underlying technical references. Clicking citation badges highlights the document page or isolates the corresponding CAD layers.",
    "workflows": [
      "Click citation badge",
      "Highlight specific PDF page/line",
      "Trigger viewer layer filter"
    ],
    "dependencies": [
      "RAG sources metadata structures",
      "Workspace Preview controller"
    ]
  },
  {
    "id": "preview_workspace",
    "title": "Engineering Preview Workspace",
    "category": "Visualization",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "Visualization",
      "Workspace",
      "Productivity"
    ],
    "description": "Integrated side-by-side split viewport containing PDF Code Viewer, DXF SVG canvas, and BOQ spreadsheet.",
    "fullDescription": "Implements an adjustable panel workspace. Displays regulations, structural floor plans, and live schedules synchronously to streamline compliance audits.",
    "workflows": [
      "Query CAD layouts",
      "Toggle split columns",
      "Inspect Excel BOQ list and DXF viewer"
    ],
    "dependencies": [
      "Draggable resizers",
      "SVG layout rendering",
      "BOQ stylesheet engine"
    ]
  },
  {
    "id": "reasoner_timeline",
    "title": "AI Reasoner Trace Timeline",
    "category": "Observability",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "Observability",
      "Performance",
      "Developer"
    ],
    "description": "Visual timeline tracking durations, logs, and cosine margins of specialised backend agents.",
    "fullDescription": "Exposes agent workflows in real-time. Logs execution telemetry for step-by-step auditing (Planner, Classifier, Routing, Compliance check, Hallucination filter).",
    "workflows": [
      "Submit chat query",
      "Render active agent status",
      "Toggle Dev Debug mode for similarity telemetry"
    ],
    "dependencies": [
      "Backend execution profiling",
      "State machine transition events"
    ]
  },
  {
    "id": "model_selector",
    "title": "LLM Provider Selection",
    "category": "Customization",
    "product": "archchat",
    "status": "implemented",
    "tags": [
      "AI",
      "Customization",
      "Developer"
    ],
    "description": "Switch between local Ollama installations and cloud backends (Cohere/OpenAI).",
    "fullDescription": "Exposes model endpoints to optimize speed or accuracy. Queries active local Ollama tags and default cloud integrations dynamically.",
    "workflows": [
      "Query active model list",
      "Select provider (Ollama Local/Cloud, HuggingFace)",
      "Trigger failover logic on router"
    ],
    "dependencies": [
      "Ollama API config",
      "HF/OpenAI Token headers"
    ]
  },
  {
    "id": "text_to_dxf",
    "title": "Text-to-CAD Generation",
    "category": "CAD",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "CAD",
      "AI",
      "DXF"
    ],
    "description": "Generates complete CAD-compliant DXF drawings directly from natural language design prompts.",
    "fullDescription": "Translates design prompts into structured layout specifications. Employs deterministic planners to draft structural elements, wall systems, and labels.",
    "workflows": [
      "Describe floor plan",
      "Parse prompt to rooms/openings structure",
      "Write drawing database to DXF file"
    ],
    "dependencies": [
      "ezdxf library",
      "Design parser orchestrator"
    ]
  },
  {
    "id": "layout_planner",
    "title": "Deterministic Layout Planner",
    "category": "CAD",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "CAD",
      "Performance"
    ],
    "description": "Calculates room placement spatial grids using topology scoring and zoning bounds.",
    "fullDescription": "A pure geometric solver placing rooms inside boundaries based on adjacencies. Ensures robust layouts and eliminates LLM hallucination in coordinate calculations.",
    "workflows": [
      "Construct boundary polygon",
      "Solve room layout placement",
      "Adjust room areas and boundaries"
    ],
    "dependencies": [
      "Deterministic layout logic",
      "Area balancing solver"
    ]
  },
  {
    "id": "iterative_editing",
    "title": "Iterative CAD Layout Modification",
    "category": "CAD",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "CAD",
      "AI",
      "Productivity"
    ],
    "description": "Surgically edit generated floor plans using simple natural language text edits.",
    "fullDescription": "Enables conversational CAD revisions. Compares modification requests against the active plan structure using a diff orchestrator, updating layers without rewriting the layout.",
    "workflows": [
      "Provide adjustment text",
      "Run layout diff orchestrator",
      "Surgically revise geometry elements",
      "Regenerate DXF"
    ],
    "dependencies": [
      "Iterative design service",
      "Layout Intent schemas"
    ]
  },
  {
    "id": "quality_gate",
    "title": "Architectural Compliance Gate",
    "category": "Security",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "Security",
      "CAD"
    ],
    "description": "Enforces Egyptian Building Code constraints, setback margins, and door widths.",
    "fullDescription": "Performs geometric auditing of room sizes, boundaries, fire egress clearances, and road setbacks. Generates warning reports and compliance scores.",
    "workflows": [
      "Scan layout metrics",
      "Verify clearances against EBC Rules",
      "Compile quality score and violations list"
    ],
    "dependencies": [
      "EBC compliance ruleset",
      "Layout Intent validator"
    ]
  },
  {
    "id": "cad_layers",
    "title": "Multi-Layer CAD Canvas",
    "category": "Visualization",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "Visualization",
      "CAD",
      "Customization"
    ],
    "description": "SVG-based interactive layout canvas featuring toggles for walls, columns, openings, and grids.",
    "fullDescription": "Exposes standard CAD layer management. Toggles walls, columns, doors, dimensions, grid patterns, crosshairs, and violations overlays.",
    "workflows": [
      "Extract DXF render coordinate data",
      "Map layers to SVG paths",
      "Toggle layer visibility filters"
    ],
    "dependencies": [
      "DXF render parser",
      "SVG layout generator"
    ]
  },
  {
    "id": "raster_export",
    "title": "Multi-Format Exports",
    "category": "Export",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "Export",
      "DXF",
      "Productivity"
    ],
    "description": "Exports floor plans to raw DXF files, raster PNGs, or print-ready PDF sheets.",
    "fullDescription": "Converts vector layouts to common formats. Renders layouts into high-resolution images or PDF documents for client printing and reviews.",
    "workflows": [
      "Select download format",
      "Convert DXF layout using matplotlib",
      "Return attachment file stream"
    ],
    "dependencies": [
      "ezdxf export integrations",
      "PDF layout engine"
    ]
  },
  {
    "id": "dxf_upload",
    "title": "DXF Upload & Visualizer",
    "category": "Export",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "Export",
      "DXF",
      "Visualization"
    ],
    "description": "Upload external DXF drawings up to 20MB for rendering inside the browser canvas.",
    "fullDescription": "Provides upload support for legacy files. Sanitizes uploaded filenames, checks sizes, parses structural drawing entities, and sends JSON render coordinates to the canvas.",
    "workflows": [
      "Upload local DXF file",
      "Parse CAD entities in Python",
      "Visualize inside browser viewer"
    ],
    "dependencies": [
      "DXF file sanitizer",
      "File token registry"
    ]
  },
  {
    "id": "canvas_navigation",
    "title": "Canvas Navigation & Zoom",
    "category": "Visualization",
    "product": "cadstudio",
    "status": "implemented",
    "tags": [
      "Visualization",
      "Customization"
    ],
    "description": "High-fidelity grid zooming, coordinate tracking, panning, and dark mode controls.",
    "fullDescription": "Binds drag/zoom listeners to the browser canvas. Features zoom-to-fit, coordinate trackers, grid rulers, and color themes.",
    "workflows": [
      "Scale canvas on scroll wheel",
      "Track cursor X/Y coordinates",
      "Toggle canvas themes"
    ],
    "dependencies": [
      "Canvas viewer Javascript controller"
    ]
  },
  {
    "id": "user_auth",
    "title": "Dual Authentication System",
    "category": "Security",
    "product": "platform",
    "status": "implemented",
    "tags": [
      "Security",
      "Workspace"
    ],
    "description": "Secure authentication using credentials or Google OAuth.",
    "fullDescription": "Secures data access with HTTP-only cookies and JWT tokens. Integrates Google Credentials (GSI) seamlessly.",
    "workflows": [
      "Sign Up / Login with Email",
      "Google GSI One-Tap authentication",
      "Verify JWT middleware cookie"
    ],
    "dependencies": [
      "SQLite auth schema",
      "JWT credentials manager"
    ]
  },
  {
    "id": "guest_access",
    "title": "Anonymous Guest Workspaces",
    "category": "Workspace",
    "product": "platform",
    "status": "implemented",
    "tags": [
      "Workspace"
    ],
    "description": "Create layouts and projects instantly without account registration.",
    "fullDescription": "Maintains guest sessions via temporary cookie tokens. Keeps workspace databases and output storage folders completely isolated.",
    "workflows": [
      "Launch studio as guest",
      "Generate temporary workspace ID",
      "Prune cookie on session expiry"
    ],
    "dependencies": [
      "Guest workspace cookie middleware"
    ]
  },
  {
    "id": "metrics",
    "title": "Observability & Profiling",
    "category": "Observability",
    "product": "platform",
    "status": "implemented",
    "tags": [
      "Observability",
      "Performance",
      "Developer"
    ],
    "description": "Exposes performance metrics (requests, RAM, uptime) and cProfile tracing.",
    "fullDescription": "Implements profiling endpoints. Returns process latency headers, RSS/VMS memory statistics, active request tracking, and cProfile diagnostics via headers.",
    "workflows": [
      "Fetch metrics endpoint",
      "Profile path latency in middleware",
      "Extract heap stats"
    ],
    "dependencies": [
      "psutil wrapper",
      "Profiling middleware"
    ]
  },
  {
    "id": "health_checks",
    "title": "Health Diagnostics API",
    "category": "Observability",
    "product": "platform",
    "status": "implemented",
    "tags": [
      "Observability",
      "Developer"
    ],
    "description": "Real-time connection verification for SQLite, Qdrant vectors, and Ollama tags.",
    "fullDescription": "Aggregates core engine diagnostics. Queries health check endpoints to report status details for SQLite DBs, local vector stores, and the Ollama model tags.",
    "workflows": [
      "Query health endpoint",
      "Verify database ping",
      "Check local Ollama daemon tags"
    ],
    "dependencies": [
      "Sub-service health checks"
    ]
  },
  {
    "id": "cleanup_loop",
    "title": "Automated Storage Cleanup",
    "category": "Performance",
    "product": "platform",
    "status": "implemented",
    "tags": [
      "Performance",
      "Developer"
    ],
    "description": "Background worker cleaning temporary drawings and documents every 6 hours.",
    "fullDescription": "Saves disk space automatically. A background lifespan thread worker inspects the backend output paths, pruning files that exceed retention settings.",
    "workflows": [
      "Startup background loop",
      "Scan temporary generated outputs",
      "Prune old CAD drawings"
    ],
    "dependencies": [
      "FastAPI lifespan context manager"
    ]
  },
  {
    "id": "realtime_collab",
    "title": "Real-Time Collaborative Workspace",
    "category": "Collaboration",
    "product": "platform",
    "status": "coming-soon",
    "stage": "In Progress",
    "tags": [
      "Realtime",
      "Workspace",
      "Collaboration"
    ],
    "description": "Co-authoring floor plans with teammates via WebSockets.",
    "fullDescription": "Synchronous co-editing of design intents. Features live cursors, overlay measurements, sync markers, and visual workspace conflict-free resolution layers.",
    "workflows": [
      "Join workspace session",
      "Live sync editing updates",
      "Conflict resolution merges"
    ],
    "dependencies": [
      "WebSocket protocols",
      "Shared CRDT document models"
    ]
  },
  {
    "id": "threejs_walkthrough",
    "title": "WebGL 3D Floor Plan Walkthroughs",
    "category": "Visualization",
    "product": "cadstudio",
    "status": "coming-soon",
    "stage": "Planned",
    "tags": [
      "Visualization",
      "CAD"
    ],
    "description": "Renders 2D lines into interactive 3D rooms using Three.js.",
    "fullDescription": "Adds WebGL model generation. Automatically converts layout wall vectors and opening constraints into 3D shapes to inspect designs virtually.",
    "workflows": [
      "Generate 2D layout",
      "Construct 3D geometry",
      "Walk through room model in browser"
    ],
    "dependencies": [
      "Three.js / WebGL context",
      "DXF to glTF converter"
    ]
  },
  {
    "id": "material_costing",
    "title": "AI Material Cost Estimation",
    "category": "RAG",
    "product": "archchat",
    "status": "coming-soon",
    "stage": "Planned",
    "tags": [
      "RAG",
      "Data"
    ],
    "description": "Calculates local BOQ material cost sheets from vendor spec sheets.",
    "fullDescription": "Automates project cost estimations. Cross-references concrete volume and steel reinforcement specs with indexed supplier documents to compile real cost lists.",
    "workflows": [
      "Extract BOQ schedules",
      "Search supplier database",
      "Generate material cost report"
    ],
    "dependencies": [
      "Cost calculator parser",
      "Supplier vector catalog index"
    ]
  },
  {
    "id": "dwg_revit_support",
    "title": "Multi-Format CAD Import/Export",
    "category": "Export",
    "product": "cadstudio",
    "status": "coming-soon",
    "stage": "Future Vision",
    "tags": [
      "Export",
      "DXF",
      "CAD"
    ],
    "description": "Support DWG, RVT, and IFC formats for full BIM suit integration.",
    "fullDescription": "Extends file support. Allows uploading native DWG drawing documents and exporting standard Revit elements or IFC models.",
    "workflows": [
      "Upload native DWG file",
      "Convert DWG to intent specifications",
      "Export standard Revit Family families"
    ],
    "dependencies": [
      "DWG conversion library",
      "BIM/IFC schema builders"
    ]
  },
  {
    "id": "revision_history",
    "title": "Layout Revision Control",
    "category": "Workspace",
    "product": "platform",
    "status": "coming-soon",
    "stage": "Future Vision",
    "tags": [
      "Workspace",
      "History"
    ],
    "description": "Git-like version control and visual rollback logs for CAD designs.",
    "fullDescription": "Tracks design modifications visually. Allows developers to review visual layout diffs, branch plans, and rollback layouts safely.",
    "workflows": [
      "Save design version checkpoint",
      "Inspect visual diff logs",
      "Restore earlier revision plan"
    ],
    "dependencies": [
      "Git-like layout schemas",
      "Visual layout diff overlays"
    ]
  }
];
