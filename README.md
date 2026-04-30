# CadArena

<div align="center">

![CadArena Logo](./frontend/public/assets/cadarena-logo.svg)

**AI-Assisted Platform for Civil and Architectural Workflows**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![React 18+](https://img.shields.io/badge/React-18%2B-61dafb)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed)](https://www.docker.com/)

[Quick Start](#quick-start) • [Features](#features) • [Architecture](#architecture) • [Documentation](#documentation)

</div>

---

## 🎯 What is CadArena?

CadArena is an **AI-powered architectural design platform** that transforms natural language prompts into professional CAD floor plans. Whether you're an architect, engineer, or designer, CadArena streamlines your workflow with intelligent design generation, real-time preview, and compliance checking.

### The Problem We Solve

- ⏱️ **Time-consuming manual drafting** → AI generates layouts in seconds
- 🔄 **Iterative design cycles** → Chat-driven modifications
- 📋 **Building code compliance** → Automatic EBC 2023 validation
- 🌍 **Language barriers** → Arabic & English support
- 💾 **Format compatibility** → DXF export for AutoCAD/Revit

---

## ✨ Key Features

### 🏗️ Core Capabilities

```mermaid
graph LR
    A["Natural Language<br/>Prompt"] -->|AI Parser| B["Design Intent<br/>Classification"]
    B -->|Layout Engine| C["Floor Plan<br/>Generation"]
    C -->|Validator| D["EBC 2023<br/>Compliance Check"]
    D -->|Renderer| E["DXF Export<br/>+ Preview"]
    
    style A fill:#38CBEA,stroke:#71F3FF,color:#000
    style B fill:#38CBEA,stroke:#71F3FF,color:#000
    style C fill:#38CBEA,stroke:#71F3FF,color:#000
    style D fill:#38CBEA,stroke:#71F3FF,color:#000
    style E fill:#38CBEA,stroke:#71F3FF,color:#000
```

### 🎨 Platform Features

| Feature | Description |
| --- | --- |
| **AI-Powered Generation** | Convert prompts to professional floor plans instantly |
| **Real-time Preview** | See changes as you describe them |
| **DXF Export** | Compatible with AutoCAD, Revit, and other CAD tools |
| **EBC 2023 Compliance** | Automatic validation against Egyptian Building Code |
| **Community Q&A** | Share knowledge and get answers from architects |
| **Multi-language** | Arabic and English support |
| **Responsive Design** | Works on desktop, tablet, and mobile |
| **WCAG 2.1 AA** | Fully accessible to all users |

---

## 🏛️ Architecture Overview

### System Architecture

```mermaid
graph TB
    subgraph Frontend["🎨 Frontend (React)"]
        UI["React UI<br/>Components"]
        Chat["Chat Interface"]
        Preview["DXF Preview"]
        Community["Community Hub"]
    end
    
    subgraph Backend["⚙️ Backend (FastAPI)"]
        Router["Intent Router"]
        Parser["Design Parser"]
        Validator["Layout Validator"]
        Renderer["DXF Renderer"]
    end
    
    subgraph Storage["💾 Storage"]
        DB["SQLite Database"]
        Files["DXF Files"]
    end
    
    UI -->|HTTP/WebSocket| Router
    Chat -->|Prompts| Router
    Router -->|Classify Intent| Parser
    Parser -->|Generate Layout| Validator
    Validator -->|Validate EBC| Renderer
    Renderer -->|Output| Preview
    Renderer -->|Save| Files
    Router -->|User Data| DB
    Community -->|Q&A| DB
    
    style Frontend fill:#61dafb,stroke:#0891b2,color:#000
    style Backend fill:#009688,stroke:#00695c,color:#fff
    style Storage fill:#ff9800,stroke:#e65100,color:#fff
```

### Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Parser
    participant Validator
    participant Renderer
    
    User->>Frontend: "3 bedroom apartment 100 sqm"
    Frontend->>Backend: POST /design/generate
    Backend->>Parser: Parse intent & extract specs
    Parser->>Parser: Generate layout
    Parser->>Validator: Validate against EBC 2023
    
    alt Compliant
        Validator->>Renderer: Render to DXF
        Renderer->>Frontend: Return preview + file
        Frontend->>User: Display floor plan
    else Non-compliant
        Validator->>Backend: Return violations
        Backend->>Frontend: Suggest modifications
        Frontend->>User: "Adjust room sizes..."
    end
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.12+
- **Node.js** 18+
- **npm** or **yarn**
- **Docker** (optional)

### Option 1: Local Development

#### Backend Setup

```bash
cd backend

# Setup environment
cp .env.example .env

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

#### Access the Application

- **React App**: http://localhost:3000
- **Studio**: http://localhost:3000/studio
- **Community**: http://localhost:3000/community
- **API Docs**: http://127.0.0.1:8000/docs

### Option 2: Docker Deployment

```bash
# From project root
docker compose -f docker/docker-compose.yml up --build

# Access at http://localhost:8000
```

---

## 📁 Project Structure

```
CadArena/
├── 📂 backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                      # Application entry point
│   │   ├── routes/                      # API endpoints
│   │   ├── models/                      # Database models
│   │   ├── schemas/                     # Pydantic schemas
│   │   ├── services/
│   │   │   ├── design_parser/           # Layout generation engine
│   │   │   │   ├── layout_planner.py    # Spatial planning
│   │   │   │   ├── layout_validator.py  # EBC compliance
│   │   │   │   ├── opening_planner.py   # Door/window placement
│   │   │   │   └── egyptian_building_code.py  # EBC constants
│   │   │   ├── intent_router.py         # Intent classification
│   │   │   └── dxf_room_renderer.py     # DXF generation
│   │   ├── utils/
│   │   │   └── design_prompt.py         # System prompts
│   │   └── tests/                       # Test suite
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── 📂 frontend/                         # React application
│   ├── src/
│   │   ├── components/                  # Reusable components
│   │   ├── pages/                       # Page components
│   │   ├── hooks/                       # Custom hooks
│   │   ├── utils/                       # Utilities
│   │   ├── styles/                      # Global styles
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   │   ├── assets/                      # Logo & images
│   │   └── studio-app/                  # Legacy studio
│   ├── package.json
│   ├── tailwind.config.js
│   ├── jest.config.js
│   └── README.md
│
├── 📂 docker/                           # Container setup
│   ├── Dockerfile                       # Multi-stage build
│   ├── docker-compose.yml               # Compose config
│   └── README.md
│
├── 📂 docs/                             # Documentation
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DESIGN.md
│
├── .dockerignore
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🛠️ Tech Stack

### Backend

| Technology | Version | Purpose |
| --- | --- | --- |
| **Python** | 3.12+ | Core language |
| **FastAPI** | 0.100+ | Web framework |
| **SQLAlchemy** | 2.0+ | ORM |
| **Pydantic** | 2.0+ | Data validation |
| **Uvicorn** | 0.23+ | ASGI server |
| **pytest** | 7.0+ | Testing |

### Frontend

| Technology | Version | Purpose |
| --- | --- | --- |
| **React** | 18+ | UI framework |
| **Tailwind CSS** | 3.0+ | Styling |
| **Framer Motion** | 10+ | Animations |
| **Lucide React** | Latest | Icons |
| **Jest** | 29+ | Testing |
| **React Testing Library** | 14+ | Component testing |

### DevOps

| Technology | Purpose |
| --- | --- |
| **Docker** | Containerization |
| **Docker Compose** | Orchestration |
| **Git** | Version control |

---

## 🧪 Testing

### Run Tests

```bash
# Backend tests
cd backend
pytest app/tests -v

# Frontend tests
cd frontend
npm test

# With coverage
pytest app/tests --cov=app
npm test -- --coverage
```

### Test Coverage

- **Backend**: Unit tests, integration tests, API tests
- **Frontend**: Component tests, hook tests, utility tests
- **EBC Compliance**: 15+ test cases for building code validation

---

## 🐳 Docker Deployment

### Quick Start

```bash
docker compose -f docker/docker-compose.yml up --build
```

### Features

- ✅ Multi-stage build for optimized images
- ✅ Non-root user for security
- ✅ Health checks for monitoring
- ✅ Volume persistence for data
- ✅ Network isolation
- ✅ Environment configuration

See [docker/README.md](docker/README.md) for detailed instructions.

---

## 📚 Documentation

- **[Backend README](backend/README.md)** - API documentation and setup
- **[Frontend README](frontend/README.md)** - Component guide and development
- **[Docker README](docker/README.md)** - Deployment and containerization
- **[Architecture](docs/ARCHITECTURE.md)** - System design and decisions
- **[API Reference](docs/API.md)** - Complete API documentation

---

## 🏛️ Building Code Compliance

CadArena enforces **Egyptian Building Code (EBC 2023)** standards:

### Minimum Room Dimensions

```mermaid
graph LR
    A["Bedroom<br/>9.0 m²<br/>2.75 m min"] -->|EBC Ch.7| B["Bathroom<br/>2.5 m²<br/>1.20 m min"]
    B --> C["Kitchen<br/>4.0 m²<br/>1.80 m min"]
    C --> D["Living<br/>12.0 m²<br/>3.00 m min"]
    D --> E["Corridor<br/>1.20 m width<br/>HARD LIMIT"]
    
    style A fill:#4CAF50,stroke:#2E7D32,color:#fff
    style B fill:#4CAF50,stroke:#2E7D32,color:#fff
    style C fill:#4CAF50,stroke:#2E7D32,color:#fff
    style D fill:#4CAF50,stroke:#2E7D32,color:#fff
    style E fill:#f44336,stroke:#c62828,color:#fff
```

### Apartment Type Standards

| Type | Min Area | Typical Rooms |
| --- | --- | --- |
| **Studio** | 25–45 m² | 1 room + kitchen + bathroom |
| **1-Bedroom** | 45–75 m² | 1 bed + living + kitchen + bathroom |
| **2-Bedroom** | 75–120 m² | 2 beds + living + kitchen + bathroom |
| **3-Bedroom** | 100–160 m² | 3 beds + living + kitchen + 2 bathrooms |
| **4-Bedroom** | 140–220 m² | 4 beds + living + kitchen + 2 bathrooms |
| **Villa** | 200–500 m² | Multiple zones + outdoor spaces |

### Forbidden Adjacencies

```mermaid
graph LR
    A["❌ Bathroom"] -->|Forbidden| B["Kitchen"]
    C["❌ Bedroom"] -->|Forbidden| D["Kitchen"]
    E["❌ Bathroom"] -->|Forbidden| F["Dining"]
    
    style A fill:#f44336,stroke:#c62828,color:#fff
    style B fill:#f44336,stroke:#c62828,color:#fff
    style C fill:#f44336,stroke:#c62828,color:#fff
    style D fill:#f44336,stroke:#c62828,color:#fff
    style E fill:#f44336,stroke:#c62828,color:#fff
    style F fill:#f44336,stroke:#c62828,color:#fff
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes and commit (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow existing code style
- Write tests for new features
- Update documentation
- Ensure all tests pass
- Keep commits atomic and well-documented

---

## 🔒 Security

- Non-root Docker user
- Environment variable management
- Input validation and sanitization
- CORS configuration
- Rate limiting
- Security headers

For security concerns: security@cadarena.dev

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙋 Support & Community

### Getting Help

- 📖 [Documentation](docs/)
- 💬 [Community Discussions](https://cadarena.dev/community)
- 🐛 [Report Issues](https://github.com/cadarena/cadarena/issues)
- 💡 [Feature Requests](https://github.com/cadarena/cadarena/discussions)

### Connect With Us

- **Website**: [cadarena.dev](https://cadarena.dev)
- **Community**: [cadarena.dev/community](https://cadarena.dev/community)
- **Email**: cadarena.ai@gmail.com

---

## 🎉 Acknowledgments

Built with ❤️ using:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS
- [Framer Motion](https://www.framer.com/motion/) - Animation library
- [Lucide React](https://lucide.dev/) - Icon library
- [Jest](https://jestjs.io/) - Testing framework
- [pytest](https://pytest.org/) - Python testing

---

## 📊 Project Statistics

- **Backend**: Python + FastAPI
- **Frontend**: React + Tailwind CSS
- **Tests**: 100+ test cases
- **Components**: 20+ reusable components
- **API Endpoints**: 30+ endpoints
- **Documentation**: Comprehensive
- **Accessibility**: WCAG 2.1 AA compliant
- **Building Code**: EBC 2023 compliant

---

<div align="center">

**Made with ❤️ by the CadArena Team**

[⬆ Back to top](#cadarena)

</div>
