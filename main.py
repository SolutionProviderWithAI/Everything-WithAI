import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

"""
EverythingWithAI
Full-stack FastAPI Application serving dynamic portfolio, AI Architecture Advisor,
AJAX Contact submissions with database persistence, and REST APIs.
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# 1. Base Paths & Directories
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(DATA_DIR, "submissions.db")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 2. Database Initialization (SQLite)
# -----------------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT,
            project_type TEXT NOT NULL,
            existing_technology TEXT NOT NULL,
            project_description TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# 3. Load Portfolio Data
# -----------------------------------------------------------------------------
PORTFOLIO_FILE = os.path.join(DATA_DIR, "portfolio.json")

def load_portfolio_data() -> Dict[str, Any]:
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

portfolio_data = load_portfolio_data()

# -----------------------------------------------------------------------------
# 4. Pydantic Models (Matching OpenAPI 3.1.0 specifications)
# -----------------------------------------------------------------------------
class ContactSubmissionRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Name of the person reaching out")
    email: str = Field(..., description="Valid contact email address")
    company: Optional[str] = Field(None, max_length=100, description="Company name (optional)")
    project_type: str = Field(..., min_length=2, max_length=100, description="Type of project")
    existing_technology: str = Field(..., min_length=2, max_length=100, description="Existing software technology")
    project_description: str = Field(..., min_length=20, max_length=3000, description="Detailed project description")

class ContactSubmissionResponse(BaseModel):
    success: bool = Field(..., description="Success flag")
    message: str = Field(..., description="Status message")
    submission_id: Optional[int] = Field(None, description="Created submission ID")

class AIAdvisorRequest(BaseModel):
    existing_tech: str = Field(..., description="Client current stack, e.g. .NET Core, ASP.NET, Python")
    use_case: str = Field(..., description="Target AI use-case, e.g. document search, chatbot, automation, voice")
    database: Optional[str] = Field("SQL Server", description="Existing database")
    data_privacy_level: Optional[str] = Field("Enterprise / Private", description="Privacy constraints")

class AIAdvisorResponse(BaseModel):
    recommended_architecture: str = Field(..., description="Recommended architecture name")
    key_components: List[str] = Field(..., description="Key architectural components")
    implementation_steps: List[str] = Field(..., description="Implementation steps")
    feasibility_score: int = Field(..., description="Feasibility score out of 100")
    estimated_timeline: str = Field(..., description="Estimated timeline")
    pro_tip: str = Field(..., description="Implementation pro-tip")

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat message history")
    model: Optional[str] = Field("my-brain", description="Ollama model name (my-brain or llama3.2)")
    stream: Optional[bool] = Field(True, description="Whether to stream the response via SSE")

class ChatResponse(BaseModel):
    success: bool = Field(..., description="Success flag")
    message: str = Field(..., description="Assistant reply")
    model: str = Field(..., description="Model used")

# -----------------------------------------------------------------------------
# 5. FastAPI Application Instance
# -----------------------------------------------------------------------------
app = FastAPI(
    title="EverythingWithAI",
    description="Portfolio website for Senior .NET Developer specializing in AI & LLM Integration.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files and Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# -----------------------------------------------------------------------------
# 6. Routes
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, summary="Home", operation_id="home__get")
async def home(request: Request):
    """
    Renders the full portfolio landing page matching https://ai-solutionworldwithsujit.bolt.host/
    """
    context = {
        "request": request,
        **portfolio_data
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
    )


@app.get("/requests", response_class=HTMLResponse, summary="View Requests Page", operation_id="view_requests_page_requests_get")
async def view_requests_page(request: Request):
    """
    Dashboard to view all project requests submitted by clients.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contact_submissions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    submissions = [dict(row) for row in rows]
    context = {
        "request": request,
        "personal": portfolio_data.get("personal", {}),
        "submissions": submissions
    }
    return templates.TemplateResponse(
        request=request,
        name="requests.html",
        context=context
    )


@app.post("/api/contact", response_model=ContactSubmissionResponse, summary="Submit Contact", operation_id="submit_contact_api_contact_post")
async def submit_contact(submission: ContactSubmissionRequest):
    """
    Handles contact form submissions via AJAX with validation and database storage.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        cursor.execute(
            """
            INSERT INTO contact_submissions (
                name, email, company, project_type, existing_technology, project_description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission.name,
                submission.email,
                submission.company,
                submission.project_type,
                submission.existing_technology,
                submission.project_description,
                now_str
            )
        )
        conn.commit()
        submission_id = cursor.lastrowid
        conn.close()

        return ContactSubmissionResponse(
            success=True,
            message="Your project request has been submitted successfully! Sujit will review your inquiry shortly.",
            submission_id=submission_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record your submission: {str(e)}"
        )


@app.post("/api/advisor", response_model=AIAdvisorResponse, summary="Ai Architecture Advisor", operation_id="ai_architecture_advisor_api_advisor_post")
async def ai_architecture_advisor(req: AIAdvisorRequest):
    """
    Interactive API for clients to get instant AI architecture feasibility & recommendations.
    """
    tech = req.existing_tech or ".NET Core / C#"
    use_case = req.use_case or "RAG Document Search"
    database = req.database or "SQL Server"

    if "RAG" in use_case or "Document" in use_case:
        return AIAdvisorResponse(
            recommended_architecture="Decoupled RAG Pipeline with Semantic Search & Vector Embeddings",
            key_components=[
                f"{tech} Service Consumer via secure HTTPS / REST",
                "FastAPI / Python RAG Middleware orchestrator",
                f"{database} connector for structured metadata validation",
                "Vector Database (ChromaDB / pgvector / Azure AI Search) storing document chunk embeddings",
                "Private LLM Context Injection (OpenAI GPT-4o / Azure OpenAI) with zero data training policy"
            ],
            implementation_steps=[
                "1. Document Ingestion: Extract text from PDFs, Word documents, or database knowledge articles.",
                "2. Chunking & Embeddings: Generate dense vector embeddings using text-embedding-3-small.",
                "3. API Gateway: Expose an authenticated search endpoint for your existing application.",
                "4. Context Assembly & Prompt Guardrails: Retrieve top-k relevant chunks and synthesize verified answers."
            ],
            feasibility_score=96,
            estimated_timeline="1 to 2 weeks for Production PoC",
            pro_tip="Because your existing application consumes a dedicated REST endpoint, you avoid touching legacy monolithic code while gaining modern RAG intelligence."
        )

    elif "Agent" in use_case or "Autonomous" in use_case:
        return AIAdvisorResponse(
            recommended_architecture="Autonomous Function-Calling AI Agent Layer with API Tools",
            key_components=[
                f"Existing {tech} REST endpoints mapped as Agent Tools",
                "Structured Tool-Calling LLM Controller (OpenAI / Claude 3.5 Sonnet)",
                "Execution Guardrails & Permission Verifier (prevents unauthorized database writes)",
                f"Direct query access to {database} with read-only connection pool",
                "Async task queue (Celery / Background Tasks) for multi-step jobs"
            ],
            implementation_steps=[
                "1. Tool Definition: Expose your existing APIs as JSON Schema functions for the LLM.",
                "2. Permission Boundary: Implement strict schema verification and role-based access.",
                "3. Agent Loop: Agent parses natural language requests, plans tool invocations, and queries your backend.",
                "4. Validation & Feedback: Returns structured JSON response back to your client software."
            ],
            feasibility_score=92,
            estimated_timeline="2 to 3 weeks for full Agent workflow",
            pro_tip="Give the AI agent read-only tools first to build operational confidence before enabling write-enabled transactions."
        )

    elif "Voice" in use_case:
        return AIAdvisorResponse(
            recommended_architecture="Low-Latency Real-Time Voice AI Integration Gateway",
            key_components=[
                "Realtime WebRTC / WebSocket Audio Gateway",
                "Speech-to-Text (Whisper / Deepgram) with under 200ms turnaround",
                f"FastAPI microservice bridging call context to your {tech} API",
                f"{database} customer records verification layer",
                "Ultra-fast Text-to-Speech (ElevenLabs / Azure Neural Voice)"
            ],
            implementation_steps=[
                "1. Telephony / Voice Stream Setup: Connect SIP / Twilio / WebRTC stream to voice gateway.",
                "2. Context Retrieval: Fetch customer history from your existing database as call connects.",
                "3. Conversational AI: Stream sub-second voice responses with barge-in interruption support.",
                "4. Action Dispatch: Trigger follow-up tickets or emails directly in your CRM."
            ],
            feasibility_score=89,
            estimated_timeline="2 to 4 weeks",
            pro_tip="Optimizing latency under 600ms total loop time is critical for natural conversation flow."
        )

    else:  # Assistant Overlay
        return AIAdvisorResponse(
            recommended_architecture=f"Smart AI Assistant Overlay for {tech}",
            key_components=[
                f"{tech} UI Component (embedded modal or conversational sidebar)",
                "FastAPI Gateway managing sessions, token rate-limiting, and error handling",
                f"{database} context bridge converting natural language into verified queries",
                "LLM Prompt Orchestrator with domain-specific system prompts",
                "Secure Telemetry & Audit Logging"
            ],
            implementation_steps=[
                "1. Scope Identification: Pinpoint the top 3 friction points in user workflows.",
                "2. Middleware Setup: Deploy lightweight Python middleware to mediate between frontend and LLM.",
                "3. API Hookup: Connect existing database and endpoints as contextual sources.",
                "4. UI Integration: Add a clean chat interface into the existing application screens."
            ],
            feasibility_score=98,
            estimated_timeline="1 week for PoC, 2-3 weeks for Production",
            pro_tip="Keep the initial deployment laser-focused on one high-impact repetitive task for immediate ROI."
        )


@app.get("/api/health", summary="Health Check", operation_id="health_check_api_health_get")
async def health_check():
    """
    Liveness and readiness healthcheck probe for cloud deployment.
    """
    personal = portfolio_data.get("personal", {})
    return {
        "status": "healthy",
        "app": "EverythingWithAI",
        "version": "1.0.0",
        "developer": personal.get("name", "Sujit"),
        "role": personal.get("role", "Senior .NET Software Developer"),
        "availability": personal.get("availability", "Open")
    }


@app.get("/api/submissions", summary="Get Submissions Json", operation_id="get_submissions_json_api_submissions_get")
async def get_submissions_json():
    """
    JSON API endpoint returning recent project requests.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM contact_submissions ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    submissions = [dict(row) for row in rows]
    return {
        "count": len(submissions),
        "submissions": submissions
    }


@app.get("/api/portfolio-data", summary="Get Portfolio Data", operation_id="get_portfolio_data_api_portfolio_data_get")
async def get_portfolio_data():
    """
    Raw JSON API providing all portfolio structured data.
    """
    return portfolio_data


# -----------------------------------------------------------------------------
# 7. AI Brain Chat Endpoints (Groq Cloud Llama 3.3 / Local Ollama / Smart Knowledge Engine)
# -----------------------------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip()

LLAMA_SYSTEM_PROMPT = """You are Jarvis, the intelligent AI assistant and architecture advisor for EverythingWithAI (https://everything-withai.onrender.com/).
You assist software engineers, engineering leaders, and business owners looking to integrate modern AI into existing enterprise applications.

Knowledge Base:
- Developer & Founder: Sujit — Senior .NET Software Developer & AI/LLM Integration Specialist (15+ years of enterprise software engineering).
- Core Services:
  1. ChatGPT & LLM Integration (OpenAI, Claude, Llama, Groq, Ollama, API orchestration)
  2. Autonomous AI Agents (function calling, API tools, multi-step background workflow automation)
  3. Enterprise RAG Applications (Vector databases, ChromaDB, pgvector, Azure AI Search, secure semantic retrieval without data leakage)
  4. Voice AI (WebRTC, real-time telephony, sub-second latency speech processing)
  5. Enterprise Modernization (Infusing modern AI intelligence into existing C#, ASP.NET Core, and legacy systems without costly rebuilds)
- Core philosophy: "AI Doesn't Always Mean Rebuilding Your Application." Connect modern AI to existing databases (SQL Server, Oracle, PostgreSQL) and existing APIs.
- Contact: sandilya.sujit@gmail.com or via the "Discuss Project" form on the site.

Behavior & Tone:
- Professional, technical, concise, and helpful.
- When answering technical questions, provide practical architecture patterns and clean code snippets in C# or Python when requested.
- Keep answers engaging, structured, and easy to read with markdown.
- If a client wants to discuss a project or request a quote, encourage them to use the "Discuss Project" form on the site or reach out to sandilya.sujit@gmail.com.
"""


def get_smart_knowledge_response(query: str, history: List[Any] = None) -> str:
    q = query.lower().strip()

    if any(k in q for k in ["hi", "hello", "hey", "who are you", "what is this", "introduce", "namaste", "morning", "evening"]):
        return (
            "### Hello! Welcome to EverythingWithAI 👋\n\n"
            "I am **Jarvis**, your AI Architecture & Integration Assistant for **EverythingWithAI**.\n\n"
            "I specialize in helping software engineers, architects, and business leaders integrate modern AI capabilities into existing enterprise applications.\n\n"
            "**Here is how I can assist you today:**\n"
            "- ⚡ **LLM & ChatGPT Integration**: Seamlessly connect OpenAI, Claude, or open-source Llama to existing business APIs.\n"
            "- 🤖 **Autonomous AI Agents**: Multi-step workflow agents with structured tool-calling & permission guardrails.\n"
            "- 📚 **Enterprise RAG Systems**: Private document search across SQL Server, PDFs, and vector databases without data leakage.\n"
            "- 🎙️ **Voice AI**: Sub-second real-time conversational voice agents for customer calls and dispatching.\n"
            "- 🔄 **.NET Modernization**: Infuse AI into existing C# / ASP.NET applications without costly rebuilds.\n\n"
            "Feel free to ask a technical question, explore architecture patterns, or discuss a project!"
        )

    if any(k in q for k in [".net", "c#", "asp.net", "existing", "rebuild", "legacy", "monolith", "sql server", "rewrite"]):
        return (
            "### 🔄 AI Integration Without Rebuilding Your .NET Application\n\n"
            "Our core philosophy is: **\"AI Doesn't Always Mean Rebuilding Your Application.\"**\n\n"
            "Many organizations have robust, battle-tested software written in C#, ASP.NET, or .NET Framework. "
            "You do **not** need to discard your code or migrate to a new stack to get the benefits of AI.\n\n"
            "#### Recommended Architecture Pattern:\n"
            "1. **Decoupled AI Middleware Gateway**:\n"
            "   - Deploy a lightweight, high-performance async gateway (FastAPI or ASP.NET Core Semantic Kernel).\n"
            "   - Your existing .NET application communicates with this gateway using standard REST/JSON or gRPC.\n"
            "2. **Direct Enterprise Database Access**:\n"
            "   - The AI middleware queries your existing **SQL Server**, **PostgreSQL**, or **Oracle** database using read-only connection pools.\n"
            "3. **Zero Data Training Policy**:\n"
            "   - Customer data is passed in-memory during context injection and is never used to train public models.\n"
            "4. **C# Client Integration Example**:\n"
            "```csharp\n"
            "// Example C# HttpClient calling the AI Integration Gateway\n"
            "using var client = new HttpClient();\n"
            "var requestPayload = new {\n"
            "    user_query = \"Summarize recent transactions for account #10492\",\n"
            "    customer_context = dbContext.Customers.Find(customerId)\n"
            "};\n"
            "var response = await client.PostAsJsonAsync(\"https://ai-gateway.internal/api/advisor\", requestPayload);\n"
            "var result = await response.Content.ReadFromJsonAsync<AIResponse>();\n"
            "```\n\n"
            "Would you like to review an architecture roadmap for your specific .NET stack?"
        )

    if any(k in q for k in ["rag", "document", "search", "vector", "embedding", "chroma", "pgvector", "knowledge"]):
        return (
            "### 📚 Enterprise RAG (Retrieval-Augmented Generation)\n\n"
            "RAG allows your existing software to answer questions from internal company documents, manuals, and databases with verifiable citations and **zero hallucinations**.\n\n"
            "#### How Our Production RAG Pipeline Works:\n"
            "1. **Ingestion & Parsing**: Documents (PDFs, Word docs, confluence pages, database tables) are automatically ingested and preprocessed.\n"
            "2. **Semantic Chunking**: Content is split into semantically coherent paragraphs with overlapping windows.\n"
            "3. **Dense Vector Embeddings**: Text chunks are converted into dense vector embeddings using models like `text-embedding-3-small` or BGE.\n"
            "4. **Vector Storage**: Stored in enterprise vector stores such as **Azure AI Search**, **pgvector (PostgreSQL)**, or **ChromaDB**.\n"
            "5. **Semantic Retrieval + Guardrails**: When a user queries, the top-k most relevant excerpts are fetched and injected into the LLM system prompt with strict factual guardrails.\n\n"
            "**Key Benefit**: Fast, private, and eliminates the risk of sensitive internal data leaking to public models.\n\n"
            "Ready to test a RAG PoC on your company docs? You can submit your requirements via the **Discuss Project** form below!"
        )

    if any(k in q for k in ["agent", "autonomous", "tool", "function call", "workflow", "automate"]):
        return (
            "### 🤖 Autonomous AI Agents with API Tool-Calling\n\n"
            "Traditional chatbots only respond with text. **AI Agents take real actions** across your systems.\n\n"
            "#### Agent Architecture Components:\n"
            "- **LLM Orchestrator**: Uses function-calling (OpenAI / Claude / Llama 3.3) to interpret intent and plan multi-step actions.\n"
            "- **Tool Registry**: Your existing REST APIs (e.g. `CheckInventory`, `CreateTicket`, `SendInvoice`) are mapped as JSON Schema tools.\n"
            "- **Execution Guardrails**: Role-based access control (RBAC) and confirmation boundaries prevent unauthorized database updates or transactions.\n"
            "- **Async Task Queue**: Celery or background workers manage long-running multi-stage jobs.\n\n"
            "**Best Practice**: We always start agents with read-only tools to build team trust, before gradually enabling write-capable operations."
        )

    if any(k in q for k in ["voice", "call", "audio", "webrtc", "speech", "phone", "telephony"]):
        return (
            "### 🎙️ Low-Latency Real-Time Voice AI\n\n"
            "We build sub-second real-time voice agents suitable for customer support call handling, automated dispatch, and hands-free field operations.\n\n"
            "- **Speech-to-Text (STT)**: Deepgram / Whisper streaming audio with sub-200ms latency.\n"
            "- **LLM Reasoning**: Fast streaming models (Llama 3.3 on Groq / GPT-4o-mini) generating responses in real-time.\n"
            "- **Text-to-Speech (TTS)**: ElevenLabs / Cartesia / Azure Neural Voice delivering human-grade emotion.\n"
            "- **Barge-in Support**: Allows callers to naturally interrupt the AI assistant mid-sentence."
        )

    if any(k in q for k in ["cost", "price", "rate", "hire", "timeline", "quote", "contact", "email", "reach", "consult", "book", "meeting"]):
        return (
            "### 💼 Project Engagement & Consultation\n\n"
            "We work with companies ranging from fast-growing startups to enterprise firms on a project or consulting basis.\n\n"
            "**Typical Timelines**:\n"
            "- ⚡ **Production PoC / MVP**: 1 to 2 weeks\n"
            "- 🚀 **Full Enterprise Integration**: 3 to 6 weeks\n\n"
            "**How to Connect with Sujit**:\n"
            "- 📧 **Email**: [sandilya.sujit@gmail.com](mailto:sandilya.sujit@gmail.com)\n"
            "- 📝 **Project Form**: Use the [Discuss Project](#contact) form on this page to detail your requirements and existing tech stack.\n"
            "- 📊 **Inquiries Dashboard**: View recent submissions at [/requests](/requests).\n\n"
            "Drop a message with your project goals, and Sujit will review your architecture and provide an action plan!"
        )

    if any(k in q for k in ["sujit", "experience", "developer", "founder", "background", "about", "bio", "years"]):
        return (
            "### 👨‍💻 About Sujit — Senior .NET & AI Integration Developer\n\n"
            "- **15+ Years** of hands-on enterprise software engineering experience.\n"
            "- **Core Expertise**: Enterprise application architecture, C#, ASP.NET Core, SQL Server, Python, FastAPI, and AI/LLM integration.\n"
            "- **Specialization**: Bridging the gap between battle-tested enterprise backends and cutting-edge generative AI models (OpenAI, Claude, Llama, Ollama, vector search, autonomous agents).\n"
            "- **Location**: Remote / Worldwide.\n"
            "- **Contact**: [sandilya.sujit@gmail.com](mailto:sandilya.sujit@gmail.com)"
        )

    return (
        f"### Architecture Perspective on: \"{query}\"\n\n"
        "At **EverythingWithAI**, we focus on pragmatic, production-grade AI integration for existing business software.\n\n"
        "**Key Architecture Recommendations:**\n"
        "1. **Decouple AI from Core Business Logic**: Deploy AI capabilities as independent microservices or middleware to prevent vendor lock-in.\n"
        "2. **Maintain Strict Data Privacy**: Ensure sensitive enterprise data is sanitized and protected with zero-training enterprise APIs or private on-premise models.\n"
        "3. **Incorporate Feedback Loops**: Log model outputs and tool actions for observability, latency tracking, and prompt optimization.\n\n"
        "Would you like to explore a tailored implementation plan, or connect with Sujit at **sandilya.sujit@gmail.com** to discuss your project?"
    )


@app.get("/api/chat/status", summary="Chat Engine Status", operation_id="chat_status_api_chat_status_get")
async def chat_status():
    """
    Checks active AI brain status:
    1. Groq Cloud Llama 3.3 (if GROQ_API_KEY is configured)
    2. Local Ollama RTX 3050 (if running locally or tunneled)
    3. Built-in Smart Knowledge Engine (cloud-ready fallback)
    """
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    if groq_key:
        return {
            "online": True,
            "provider": "Groq Cloud (Llama 3.3)",
            "active_model": groq_model,
            "status_label": "Cloud Llama 3.3 Online",
            "hardware": "Groq LPU Cloud (Ultra-Fast)"
        }

    # Test local Ollama connection
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                raw_models = [m.get("name") for m in data.get("models", [])]
                preferred = "my-brain" if any("my-brain" in m for m in raw_models) else ("llama3.2" if raw_models else "llama3.2")
                return {
                    "online": True,
                    "provider": "Ollama (Local Llama Brain)",
                    "active_model": preferred,
                    "status_label": "Local RTX 3050 Online",
                    "available_models": raw_models,
                    "hardware": "NVIDIA RTX 3050 GPU"
                }
    except Exception:
        pass

    # Cloud-ready Smart Knowledge Base Assistant fallback
    return {
        "online": True,
        "provider": "Knowledge Engine (Cloud Ready)",
        "active_model": "everything-ai-v1",
        "status_label": "AI Assistant Online",
        "hardware": "Cloud / Knowledge Base"
    }


@app.post("/api/chat", summary="Chat With AI Brain", operation_id="chat_with_llama_api_chat_post")
async def chat_with_llama(req: ChatRequest):
    """
    Interactive chat endpoint with multi-tier engine:
    1. Groq Cloud Llama 3.3 (ultra-fast, 24/7 cloud execution)
    2. Local Ollama (RTX 3050 GPU)
    3. Smart Knowledge Engine (portfolio-grounded streaming fallback)
    """
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    model_name = req.model or "my-brain"

    # Assemble messages with system prompt
    formatted_messages = [{"role": "system", "content": LLAMA_SYSTEM_PROMPT}]
    last_user_query = "What services do you offer?"
    for msg in req.messages:
        if msg.role != "system":
            formatted_messages.append({"role": msg.role, "content": msg.content})
            if msg.role == "user":
                last_user_query = msg.content

    if req.stream:
        async def event_generator():
            # Tier 1: Groq Cloud Llama 3.3
            if groq_key:
                try:
                    headers = {
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": groq_model,
                        "messages": formatted_messages,
                        "temperature": 0.7,
                        "max_tokens": 1024,
                        "stream": True
                    }
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        async with client.stream(
                            "POST",
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers=headers,
                            json=payload
                        ) as response:
                            if response.status_code == 200:
                                async for line in response.aiter_lines():
                                    if not line:
                                        continue
                                    if line.startswith("data: "):
                                        data_str = line[6:].strip()
                                        if data_str == "[DONE]":
                                            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
                                            return
                                        try:
                                            chunk = json.loads(data_str)
                                            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                            if delta:
                                                yield f"data: {json.dumps({'content': delta, 'done': False})}\n\n"
                                        except Exception:
                                            continue
                                return
                            else:
                                # Groq returned error (e.g. 401 invalid key or 429 quota)
                                # Skip to Tier 3 smart fallback immediately on cloud
                                pass
                except Exception:
                    pass

            # Tier 2: Local Ollama (RTX 3050 GPU)
            try:
                async with httpx.AsyncClient(timeout=1.5) as client:
                    async with client.stream(
                        "POST",
                        f"{OLLAMA_BASE_URL}/api/chat",
                        json={
                            "model": model_name,
                            "messages": formatted_messages,
                            "stream": True,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9
                            }
                        }
                    ) as response:
                        if response.status_code == 200:
                            async for line in response.aiter_lines():
                                if not line:
                                    continue
                                try:
                                    chunk = json.loads(line)
                                    content = chunk.get("message", {}).get("content", "")
                                    is_done = chunk.get("done", False)
                                    yield f"data: {json.dumps({'content': content, 'done': is_done})}\n\n"
                                    if is_done:
                                        return
                                except Exception:
                                    continue
                            return
            except Exception:
                pass

            # Tier 3: Built-in Smart Knowledge Engine Streaming Fallback
            smart_reply = get_smart_knowledge_response(last_user_query, formatted_messages)
            words = smart_reply.split(" ")
            for i, word in enumerate(words):
                suffix = " " if i < len(words) - 1 else ""
                yield f"data: {json.dumps({'content': word + suffix, 'done': False})}\n\n"
                await asyncio.sleep(0.012)
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Non-streaming JSON response
        if groq_key:
            try:
                headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
                payload = {"model": groq_model, "messages": formatted_messages, "temperature": 0.7, "max_tokens": 1024}
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {"success": True, "message": reply, "model": groq_model}
            except Exception:
                pass

        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json={"model": model_name, "messages": formatted_messages, "stream": False})
                if resp.status_code == 200:
                    data = resp.json()
                    return {"success": True, "message": data.get("message", {}).get("content", ""), "model": model_name}
        except Exception:
            pass

        smart_reply = get_smart_knowledge_response(last_user_query, formatted_messages)
        return {"success": True, "message": smart_reply, "model": "everything-ai-v1"}



def find_available_port(preferred_port: int = 8000) -> int:
    import socket
    ports_to_test = [preferred_port, 8080, 8001, 8000, 5000, 3000]
    for p in ports_to_test:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', p))
                return p
        except OSError:
            continue
    return preferred_port


if __name__ == '__main__':
    import uvicorn
    preferred = int(os.environ.get('PORT', 8000))
    port = find_available_port(preferred)

    print("\n" + "=" * 60)
    print("  [OK] EverythingWithAI Server Launching...")
    if port != preferred:
        print(f"  [NOTICE] Port {preferred} was in use or locked by Windows.")
        print(f"  --> Automatically bound to open port: {port}")
    print(f"  >> URL: http://localhost:{port}")
    print(f"  >> Swagger API Docs: http://localhost:{port}/docs")
    print("  >> Local Llama Brain: Connected via Ollama")
    print("=" * 60 + "\n")

    uvicorn.run('main:app', host='0.0.0.0', port=port, reload=True)
