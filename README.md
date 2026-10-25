# EverythingWithAI

A modern, high-performance portfolio website and AI Integration platform for **Sujit**, Senior .NET Software Developer specializing in AI & LLM Integration.

Live URL: [https://everything-withai.onrender.com/](https://everything-withai.onrender.com/)

---

## 🌟 Features & Highlights

- **Modern Cyber & Dark UI**: Crafted with responsive Tailwind CSS, custom glowing ambient backdrop, JetBrains Mono & Inter typography, and Lucide icons.
- **Full-Stack Architecture**: Powered by **FastAPI (Python)** with Jinja2 server-side rendering, SQLite database persistence, and RESTful APIs.
- **Interactive AI Architecture Advisor**: Dynamic feasibility advisor tool that analyzes a client's existing stack (.NET, Python, Java, Node.js), database (SQL Server, Oracle, PostgreSQL), and target use case (RAG, Agents, Voice AI) to output custom architecture blueprints, timeline estimates, and feasibility scores.
- **Llama Brain AI Chat Assistant**: Interactive AI chat widget powered by local **Meta Llama 3.2** (`my-brain` / `llama3.2`) running on local NVIDIA GPU via Ollama, featuring real-time Server-Sent Events (SSE) streaming, markdown formatting, syntax highlighted code blocks with one-click copy, and persistent conversation history.
- **AJAX Project Inquiry System**: Client contact form with real-time field validation, asynchronous submission, and persistent database storage.
- **Client Inquiries Dashboard**: `/requests` administrative view and `/api/submissions` JSON endpoint for tracking received project inquiries.
- **Standalone Static & Cloud Ready**: Fully operational as a standalone static site (`index.html`) or as a containerized FastAPI application with included `Dockerfile` and `render.yaml`.

---

## 📁 Project Structure

```text
EverythingWithAI/
├── data/
│   ├── portfolio.json        # Structured portfolio data (projects, experience, tech stack, FAQs)
│   └── submissions.db        # SQLite database storing contact inquiries (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css         # Custom animations, card surfaces, gradients & scrollbars
│   ├── images/
│   │   └── favicon.svg       # Brand monogram SVG favicon
│   └── js/
│       └── script.js         # Mobile nav, accordion, AJAX form & AI Advisor frontend logic
├── templates/
│   ├── base.html             # Shared layout template with nav, footer, ambient effects & meta tags
│   ├── index.html            # Main portfolio landing page template
│   └── requests.html         # Inquiries dashboard template
├── Dockerfile                # Production container specification (Python 3.11 slim)
├── index.html                # Pre-rendered static landing page (for static hosting / preview)
├── main.py                   # FastAPI application, REST endpoints, Pydantic models & SQLite handler
├── openapi.json              # Complete OpenAPI 3.1.0 specification
├── render.yaml               # Infrastructure-as-code configuration for Render deployment
├── requests.html             # Pre-rendered static requests dashboard
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🚀 Running the Project

### Option 1: Run with Python & FastAPI (Full-Stack Mode)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the FastAPI development server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

3. **Open in browser**:
   - Portfolio Landing Page: [http://localhost:8000](http://localhost:8000)
   - Client Inquiries Dashboard: [http://localhost:8000/requests](http://localhost:8000/requests)
   - Interactive Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc API Documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option 2: Run as Static Site (Frontend-Only Mode)

Double-click `index.html` in your file explorer, or serve via any static HTTP server:
```bash
python -m http.server 8000
# or
npx serve .
```

---

### Option 3: Run with Docker

1. **Build image**:
   ```bash
   docker build -t sujit-portfolio .
   ```

2. **Run container**:
   ```bash
   docker run -p 8000:8000 sujit-portfolio
   ```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Renders the main portfolio landing page |
| `GET` | `/requests` | Renders the client inquiry dashboard |
| `POST` | `/api/contact` | Submits a project inquiry (validated and stored in SQLite) |
| `POST` | `/api/advisor` | Returns instant AI architecture feasibility & recommendations |
| `GET` | `/api/submissions` | JSON endpoint returning all recorded client requests |
| `GET` | `/api/portfolio-data`| Structured JSON of Sujit's portfolio, solutions, and tech stack |
| `POST` | `/api/chat` | Real-time chat endpoint with Llama Brain (supports SSE streaming) |
| `GET` | `/api/chat/status` | Health & model discovery endpoint for local Llama Brain |
| `GET` | `/api/health` | Health check probe returning deployment & service status |
| `GET` | `/openapi.json` | OpenAPI 3.1.0 schema specification |

---

## 🛠️ Built With

- **Backend**: Python 3, FastAPI, Uvicorn, Jinja2, SQLite
- **Frontend**: HTML5, Vanilla JavaScript (ES6+), Tailwind CSS, Lucide Icons
- **Deployment**: Docker, Render
