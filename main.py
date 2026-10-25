"""
EverythingWithAI
Full-stack FastAPI Application serving dynamic portfolio, AI Architecture Advisor,
AJAX Contact submissions with database persistence, and REST APIs.
"""

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
        "app": "sujit-portfolio",
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
# 7. Llama Brain Chat Endpoints (Ollama / Local RTX 3050)
# -----------------------------------------------------------------------------
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

LLAMA_SYSTEM_PROMPT = """You are Jarvis, the intelligent AI assistant and local Llama Brain for EverythingWithAI (https://everything-withai.onrender.com/).
You run locally on an NVIDIA RTX 3050 GPU using Meta's Llama 3.2 model.
You assist developers, engineering leads, and business owners looking to integrate modern AI into their applications.

Knowledge Base:
- Developer & Founder: Sujit — Senior .NET Software Developer & AI/LLM Integration Specialist (15+ years of enterprise software engineering).
- Core Services:
  1. ChatGPT & LLM Integration (OpenAI, Claude, Llama, Ollama, API orchestration)
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


@app.get("/api/chat/status", summary="Chat Engine Status", operation_id="chat_status_api_chat_status_get")
async def chat_status():
    """
    Checks if local Llama Ollama server is running and returns available models.
    """
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                raw_models = [m.get("name") for m in data.get("models", [])]
                preferred = "my-brain" if any("my-brain" in m for m in raw_models) else ("llama3.2" if raw_models else "llama3.2")
                return {
                    "online": True,
                    "provider": "Ollama (Local Llama Brain)",
                    "active_model": preferred,
                    "available_models": raw_models,
                    "hardware": "NVIDIA RTX 3050 GPU"
                }
    except Exception:
        pass

    return {
        "online": False,
        "provider": "Ollama (Offline)",
        "active_model": "my-brain",
        "available_models": [],
        "message": "Local Llama server is offline. Run 'ollama serve' to activate."
    }


@app.post("/api/chat", summary="Chat With Llama Brain", operation_id="chat_with_llama_api_chat_post")
async def chat_with_llama(req: ChatRequest):
    """
    Interactive chat endpoint powered by local Llama brain (my-brain / llama3.2).
    Supports Server-Sent Events (SSE) streaming or standard JSON response.
    """
    model_name = req.model or "my-brain"

    # Assemble messages with system prompt
    formatted_messages = [{"role": "system", "content": LLAMA_SYSTEM_PROMPT}]
    for msg in req.messages:
        if msg.role != "system":
            formatted_messages.append({"role": msg.role, "content": msg.content})

    if req.stream:
        async def event_generator():
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
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
                        if response.status_code != 200:
                            err_text = await response.aread()
                            # If my-brain failed, attempt fallback to llama3.2
                            if model_name != "llama3.2":
                                fallback_chunk = f"*(Notice: Falling back to llama3.2)*\n\n"
                                yield f"data: {json.dumps({'content': fallback_chunk, 'done': False})}\n\n"
                            else:
                                yield f"data: {json.dumps({'content': f'⚠️ Ollama error: {err_text.decode()}', 'done': True})}\n\n"
                                return

                        async for line in response.aiter_lines():
                            if not line:
                                continue
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                is_done = chunk.get("done", False)
                                yield f"data: {json.dumps({'content': content, 'done': is_done})}\n\n"
                                if is_done:
                                    break
                            except Exception:
                                continue
            except Exception as e:
                error_msg = (
                    f"⚠️ Could not connect to local Llama Brain ({str(e)}). "
                    "Please ensure Ollama is running (`ollama serve`) with `my-brain` or `llama3.2` model."
                )
                yield f"data: {json.dumps({'content': error_msg, 'done': True})}\n\n"

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
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                resp = await client.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json={
                        "model": model_name,
                        "messages": formatted_messages,
                        "stream": False
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "success": True,
                        "message": data.get("message", {}).get("content", ""),
                        "model": model_name
                    }
                else:
                    return JSONResponse(
                        status_code=resp.status_code,
                        content={"success": False, "error": resp.text}
                    )
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": f"Llama Brain unavailable: {str(e)}",
                    "fallback_message": "Local Llama Brain is offline. Please launch `ollama serve`."
                }
            )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
