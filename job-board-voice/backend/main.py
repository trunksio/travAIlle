"""
FastAPI Backend for Job Board with Voice Application
"""

import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
import httpx
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-4-1-20250805")

# FastAPI app
app = FastAPI(title="Job Board Voice API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Job(BaseModel):
    id: str
    title: str
    title_de: Optional[str] = None
    department: str
    department_de: Optional[str] = None
    description: str
    description_de: Optional[str] = None
    requirements: str
    requirements_de: Optional[str] = None
    location: str
    location_de: Optional[str] = None
    growth_path: str
    growth_path_de: Optional[str] = None
    posted_date: str
    team_size: Optional[str] = None
    team_size_de: Optional[str] = None

class ApplicationSession(BaseModel):
    job_id: str
    user_agent: Optional[str] = None

class ApplicationData(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    years_experience: Optional[str] = None
    skills: Optional[str] = None
    cover_letter: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    job_id: str
    job_title: str
    department: str
    language: str = "en"  # Language for response
    conversation_history: List[ChatMessage] = []

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.redis_subscriptions: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session {session_id}")
        
        # Start Redis subscription for this session
        task = asyncio.create_task(self.subscribe_to_updates(session_id))
        self.redis_subscriptions[session_id] = task
    
    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session {session_id}")
        
        # Cancel Redis subscription
        if session_id in self.redis_subscriptions:
            self.redis_subscriptions[session_id].cancel()
            del self.redis_subscriptions[session_id]
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
    
    async def subscribe_to_updates(self, session_id: str):
        """Subscribe to Redis updates for a specific session"""
        try:
            client = await redis.from_url(REDIS_URL, decode_responses=True)
            pubsub = client.pubsub()
            await pubsub.subscribe(f"application_updates:{session_id}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await self.send_message(session_id, data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in Redis message: {message['data']}")
        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for session {session_id}")
        except Exception as e:
            logger.error(f"Error in Redis subscription for {session_id}: {e}")
        finally:
            if 'pubsub' in locals():
                await pubsub.unsubscribe()
                await pubsub.close()
            if 'client' in locals():
                await client.close()

manager = ConnectionManager()

async def get_redis_client():
    """Get Redis client connection"""
    return await redis.from_url(REDIS_URL, decode_responses=True)

async def seed_demo_jobs():
    """Seed internal positions into Redis on startup"""
    client = await get_redis_client()
    
    jobs = [
        {
            "id": "job_001",
            "title": "Senior Project Manager",
            "title_de": "Senior Projektmanager/in",
            "department": "Operations",
            "department_de": "Betrieb",
            "description": "Lead cross-functional teams to deliver strategic initiatives across the organization. This role offers exposure to executive leadership and the opportunity to shape our operational excellence.",
            "description_de": "Führen Sie funktionsübergreifende Teams zur Umsetzung strategischer Initiativen im gesamten Unternehmen. Diese Rolle bietet Kontakt zur Geschäftsführung und die Möglichkeit, unsere operative Exzellenz mitzugestalten.",
            "requirements": "Experience in project management, strong stakeholder management skills, analytical mindset, ability to manage multiple priorities",
            "requirements_de": "Erfahrung im Projektmanagement, ausgeprägte Stakeholder-Management-Fähigkeiten, analytische Denkweise, Fähigkeit, mehrere Prioritäten zu verwalten",
            "location": "Main Campus - Building A",
            "location_de": "Hauptcampus - Gebäude A",
            "growth_path": "Leadership track with potential progression to Director of Operations",
            "growth_path_de": "Führungslaufbahn mit möglicher Beförderung zum Director of Operations",
            "posted_date": datetime.now().isoformat(),
            "team_size": "12-15 team members",
            "team_size_de": "12-15 Teammitglieder"
        },
        {
            "id": "job_002",
            "title": "Lead Data Analyst",
            "title_de": "Leitender Datenanalyst/in",
            "department": "Finance",
            "department_de": "Finanzen",
            "description": "Join our Finance team to drive data-driven decision making. You'll work directly with CFO leadership to provide insights that shape our financial strategy.",
            "description_de": "Werden Sie Teil unseres Finanzteams und treiben Sie datengestützte Entscheidungen voran. Sie arbeiten direkt mit der CFO-Führung zusammen, um Erkenntnisse zu liefern, die unsere Finanzstrategie prägen.",
            "requirements": "Strong analytical skills, experience with financial modeling, proficiency in data visualization tools, understanding of business metrics",
            "requirements_de": "Ausgeprägte analytische Fähigkeiten, Erfahrung mit Finanzmodellierung, Kompetenz in Datenvisualisierungstools, Verständnis von Geschäftsmetriken",
            "location": "Main Campus - Building B",
            "location_de": "Hauptcampus - Gebäude B",
            "growth_path": "Analytics leadership path with exposure to strategic planning",
            "growth_path_de": "Analytik-Führungspfad mit Einblick in die strategische Planung",
            "posted_date": datetime.now().isoformat(),
            "team_size": "5-7 team members",
            "team_size_de": "5-7 Teammitglieder"
        },
        {
            "id": "job_003",
            "title": "Product Owner",
            "title_de": "Product Owner",
            "department": "Digital Innovation",
            "department_de": "Digitale Innovation",
            "description": "Drive the product vision for our internal digital transformation initiatives. You'll collaborate with IT and business units to modernize our employee experience.",
            "description_de": "Treiben Sie die Produktvision für unsere internen digitalen Transformationsinitiativen voran. Sie arbeiten mit IT und Geschäftseinheiten zusammen, um unsere Mitarbeitererfahrung zu modernisieren.",
            "requirements": "Product management mindset, understanding of agile methodologies, ability to translate business needs to technical requirements, strong communication skills",
            "requirements_de": "Produktmanagement-Mentalität, Verständnis agiler Methoden, Fähigkeit, Geschäftsanforderungen in technische Anforderungen zu übersetzen, starke Kommunikationsfähigkeiten",
            "location": "Tech Hub - Flexible",
            "location_de": "Tech Hub - Flexibel",
            "growth_path": "Product leadership with opportunity to shape digital strategy",
            "growth_path_de": "Produktführung mit der Möglichkeit, die digitale Strategie mitzugestalten",
            "posted_date": datetime.now().isoformat(),
            "team_size": "8-10 team members",
            "team_size_de": "8-10 Teammitglieder"
        },
        {
            "id": "job_004",
            "title": "Team Lead - Customer Success",
            "title_de": "Teamleiter/in - Kundenerfolg",
            "department": "Customer Experience",
            "department_de": "Kundenerfahrung",
            "description": "Lead a team dedicated to ensuring customer satisfaction and retention. This people-focused role combines leadership with hands-on customer engagement.",
            "description_de": "Führen Sie ein Team, das sich der Kundenzufriedenheit und -bindung widmet. Diese personenzentrierte Rolle kombiniert Führung mit praktischem Kundenengagement.",
            "requirements": "Leadership experience or potential, customer-centric mindset, problem-solving skills, ability to mentor and develop others",
            "requirements_de": "Führungserfahrung oder -potenzial, kundenorientierte Denkweise, Problemlösungsfähigkeiten, Fähigkeit, andere zu betreuen und zu entwickeln",
            "location": "Any Regional Office",
            "location_de": "Jedes Regionalbüro",
            "growth_path": "Management track with path to Head of Customer Success",
            "growth_path_de": "Management-Laufbahn mit Weg zum Head of Customer Success",
            "posted_date": datetime.now().isoformat(),
            "team_size": "8-12 team members",
            "team_size_de": "8-12 Teammitglieder"
        },
        {
            "id": "job_005",
            "title": "IT-Systemadministrator/in",
            "title_de": "IT-Systemadministrator/in",
            "department": "Information Technology",
            "department_de": "Informationstechnologie",
            "description": "Manage and maintain our IT infrastructure, ensuring optimal performance and security. Support our digital workplace initiatives and cloud migration projects.",
            "description_de": "Verwalten und warten Sie unsere IT-Infrastruktur und gewährleisten Sie optimale Leistung und Sicherheit. Unterstützen Sie unsere Digital Workplace-Initiativen und Cloud-Migrationsprojekte.",
            "requirements": "Experience with Windows/Linux administration, cloud platforms (AWS/Azure), network management, security best practices, ITIL knowledge preferred",
            "requirements_de": "Erfahrung mit Windows/Linux-Administration, Cloud-Plattformen (AWS/Azure), Netzwerkmanagement, Security Best Practices, ITIL-Kenntnisse von Vorteil",
            "location": "Berlin Office",
            "location_de": "Büro Berlin",
            "growth_path": "Technical specialist track with opportunity to lead infrastructure team",
            "growth_path_de": "Technischer Spezialistenpfad mit der Möglichkeit, das Infrastrukturteam zu leiten",
            "posted_date": datetime.now().isoformat(),
            "team_size": "6-8 team members",
            "team_size_de": "6-8 Teammitglieder"
        },
        {
            "id": "job_006",
            "title": "Personalentwickler/in",
            "title_de": "Personalentwickler/in",
            "department": "Human Resources",
            "department_de": "Personalwesen",
            "description": "Shape our learning and development programs to foster employee growth. Design training initiatives, career development paths, and succession planning strategies.",
            "description_de": "Gestalten Sie unsere Lern- und Entwicklungsprogramme zur Förderung des Mitarbeiterwachstums. Entwickeln Sie Schulungsinitiativen, Karriereentwicklungspfade und Nachfolgeplanungsstrategien.",
            "requirements": "Experience in L&D, adult learning principles, program design and evaluation, coaching skills, change management expertise",
            "requirements_de": "Erfahrung in L&D, Prinzipien der Erwachsenenbildung, Programmgestaltung und -bewertung, Coaching-Fähigkeiten, Change-Management-Expertise",
            "location": "Munich Office",
            "location_de": "Büro München",
            "growth_path": "HR leadership path with potential to become Head of Talent Development",
            "growth_path_de": "HR-Führungspfad mit Potenzial zum Head of Talent Development",
            "posted_date": datetime.now().isoformat(),
            "team_size": "4-6 team members",
            "team_size_de": "4-6 Teammitglieder"
        }
    ]
    
    for job in jobs:
        await client.hset(f"job:{job['id']}", mapping=job)
        await client.sadd("all_jobs", job['id'])
    
    await client.close()
    logger.info(f"Seeded {len(jobs)} demo jobs")

@app.on_event("startup")
async def startup_event():
    """Initialize demo data on startup"""
    await seed_demo_jobs()
    logger.info("Job Board backend started")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "job-board-backend"}

@app.get("/api/jobs", response_model=List[Job])
async def get_jobs():
    """Get all available jobs"""
    client = await get_redis_client()
    
    try:
        # Get all job IDs
        job_ids = await client.smembers("all_jobs")
        
        jobs = []
        for job_id in job_ids:
            job_data = await client.hgetall(f"job:{job_id}")
            if job_data:
                jobs.append(Job(**job_data))
        
        # Sort by posted_date (newest first)
        jobs.sort(key=lambda x: x.posted_date, reverse=True)
        
        return jobs
    finally:
        await client.close()

@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """Get specific job details"""
    client = await get_redis_client()
    
    try:
        job_data = await client.hgetall(f"job:{job_id}")
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return Job(**job_data)
    finally:
        await client.close()

@app.post("/api/sessions/create")
async def create_session(session_data: ApplicationSession):
    """Create a new application session"""
    session_id = str(uuid.uuid4())
    
    client = await get_redis_client()
    
    try:
        # Store session data
        await client.hset(f"session:{session_id}", mapping={
            "job_id": session_data.job_id,
            "created_at": datetime.now().isoformat(),
            "user_agent": session_data.user_agent or ""
        })
        await client.expire(f"session:{session_id}", 3600)  # Expire after 1 hour
        
        return {
            "session_id": session_id,
            "job_id": session_data.job_id,
            "mcp_server_url": MCP_SERVER_URL
        }
    finally:
        await client.close()

@app.get("/api/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    """Get current application status for a session"""
    client = await get_redis_client()
    
    try:
        # Get session data
        session_data = await client.hgetall(f"session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get application data
        app_data = await client.hgetall(f"application:{session_id}")
        
        # Calculate completion
        required_fields = ["name", "email", "phone"]
        filled_fields = [f for f in required_fields if f in app_data]
        completion = (len(filled_fields) / len(required_fields)) * 100
        
        return {
            "session_id": session_id,
            "job_id": session_data.get("job_id"),
            "application_data": app_data,
            "completion_percentage": completion,
            "filled_fields": list(app_data.keys()),
            "required_fields": required_fields
        }
    finally:
        await client.close()

@app.post("/api/applications/submit")
async def submit_application(session_id: str):
    """Submit the application (called after voice interview completion)"""
    # This endpoint can be called to finalize the application
    # The actual submission is handled by the MCP tool
    
    client = await get_redis_client()
    
    try:
        # Check if application was already submitted
        app_data = await client.hgetall(f"application:{session_id}")
        
        if not app_data:
            # Check if it was already submitted
            session_data = await client.hgetall(f"session:{session_id}")
            if session_data and session_data.get("submitted"):
                return {
                    "success": True,
                    "message": "Application already submitted"
                }
            
            raise HTTPException(status_code=404, detail="No application data found")
        
        return {
            "success": True,
            "message": "Application ready for submission",
            "data": app_data
        }
    finally:
        await client.close()

@app.get("/api/applications")
async def get_applications(job_id: Optional[str] = None):
    """Get submitted applications (admin endpoint)"""
    client = await get_redis_client()
    
    try:
        applications = []
        
        if job_id:
            # Get applications for specific job
            app_ids = await client.lrange(f"job_applications:{job_id}", 0, -1)
            
            for app_id in app_ids:
                app_data = await client.hgetall(f"submitted_application:{app_id}")
                if app_data:
                    applications.append(app_data)
        else:
            # Get all applications (scan pattern)
            cursor = 0
            while True:
                cursor, keys = await client.scan(
                    cursor, 
                    match="submitted_application:*", 
                    count=100
                )
                
                for key in keys:
                    app_data = await client.hgetall(key)
                    if app_data:
                        applications.append(app_data)
                
                if cursor == 0:
                    break
        
        # Sort by submission date
        applications.sort(
            key=lambda x: x.get("submitted_at", ""), 
            reverse=True
        )
        
        return {"applications": applications, "count": len(applications)}
    finally:
        await client.close()

@app.post("/api/chat")
async def chat_with_claude(request: ChatRequest):
    """Chat with Claude to help build job application"""
    
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API not configured")
    
    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    redis_client = await get_redis_client()
    
    try:
        # Build the system prompt based on language
        if request.language == "de":
            system_prompt = f"""Du bist ein hilfreicher Karriereberater-Assistent, der jemandem bei der Bewerbung für eine interne Position hilft.

Aktuelle Positionsdetails:
- Stellenbezeichnung: {request.job_title}
- Abteilung: {request.department}

Deine Aufgabe ist es:
1. Dem Kandidaten zu helfen, seine Schlüsselkompetenzen und Erfahrungen relevant für diese Position zu artikulieren
2. Ihm zu helfen, eine überzeugende Aussage zu formulieren, warum er gut geeignet ist
3. Relevante Informationen aus seinem Lebenslauf oder Erfahrungsbeschreibungen zu extrahieren
4. Klärende Fragen zu stellen, um seinen Hintergrund besser zu verstehen
5. Ermutigende und konstruktive Rückmeldungen zu geben

Wenn du genügend Informationen hast, um ein Feld auszufüllen, verwende EXAKT dieses Format:

Schlüsselkompetenzen & Erfahrung:
[Schreibe den eigentlichen Inhalt hier ohne Markdown oder erklärenden Text]

Warum Sie gut geeignet sind:
[Schreibe den eigentlichen Inhalt hier ohne Markdown oder erklärenden Text]

WICHTIG:
- Verwende KEINE Markdown-Formatierung (keine **, *, oder __ Symbole) im Feldinhalt
- Füge KEINE erklärenden Phrasen wie "Hier ist was ich eintragen werde" im Feldinhalt ein
- Gib nur den sauberen, professionellen Text an, der direkt in das Formular eingehen soll
- Der Inhalt sollte fertig zum Absenden sein, ohne weitere Bearbeitung

Felder zum Ausfüllen:
- Schlüsselkompetenzen & Erfahrung (ein Absatz, der relevante Fähigkeiten beschreibt)
- Warum Sie gut geeignet sind (ein Absatz, der die Eignung für die Rolle erklärt)

Sei gesprächig, unterstützend und professionell. Denke daran, dass dies für eine interne Position ist, also arbeitet die Person bereits im Unternehmen.

ANTWORTE IMMER AUF DEUTSCH."""
        else:
            system_prompt = f"""You are a helpful career coach assistant helping someone apply for an internal position.
        
Current position details:
- Job Title: {request.job_title}
- Department: {request.department}

Your role is to:
1. Help the candidate articulate their key skills and experience relevant to this position
2. Help them craft a compelling statement about why they're a good fit
3. Extract relevant information from their CV or experience descriptions
4. Ask clarifying questions to better understand their background
5. Provide encouraging and constructive feedback

When you have enough information to populate a field, use this EXACT format:

Key Skills & Experience:
[Write the actual content here without any markdown or explanatory text]

Why You're a Good Fit:
[Write the actual content here without any markdown or explanatory text]

IMPORTANT: 
- Do NOT use markdown formatting (no **, *, or __ symbols) in the field content
- Do NOT include explanatory phrases like "Here's what I'll put" in the field content
- Just provide the clean, professional text that should go directly into the form
- The content should be ready to submit as-is, without any editing needed

Fields to help populate:
- Key Skills & Experience (a paragraph describing relevant skills)
- Why You're a Good Fit (a paragraph explaining their fit for the role)

Be conversational, supportive, and professional. Remember this is for an internal position, so they already work at the company."""

        # Convert conversation history to Claude format
        messages = []
        for msg in request.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add the current message
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # Call Claude API
        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        
        assistant_message = response.content[0].text
        
        # Extract any field updates from the response
        field_updates = extract_field_updates(assistant_message, request.language)
        
        # If there are field updates, store them in Redis and notify via WebSocket
        if field_updates:
            for field, value in field_updates.items():
                await redis_client.hset(f"application:{request.session_id}", field, value)
                
                # Publish update for WebSocket
                update_message = {
                    "type": "field_update",
                    "field": field,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }
                await redis_client.publish(
                    f"application_updates:{request.session_id}",
                    json.dumps(update_message)
                )
        
        return {
            "response": assistant_message,
            "field_updates": field_updates,
            "session_id": request.session_id
        }
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await redis_client.close()

def extract_field_updates(message: str, language: str = "en") -> Dict[str, str]:
    """Extract field updates from Claude's response"""
    import re
    field_updates = {}
    
    # Clean up markdown formatting
    def clean_text(text: str) -> str:
        # Remove markdown bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # Remove *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # Remove __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # Remove _italic_
        
        # Remove quotes if the entire text is quoted
        text = text.strip()
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        if text.startswith("'") and text.endswith("'"):
            text = text[1:-1]
        
        return text.strip()
    
    # Look for explicit field content patterns
    if language == "de":
        # German patterns
        patterns_skills = [
            r"(?:Schlüsselkompetenzen(?:\s*&\s*Erfahrung)?:\s*)(.*?)(?=Warum Sie|$)",
            r"(?:Ich werde für .*?[Ss]chlüsselkompetenzen.*?eintragen:\s*)(.*?)(?=\n\n|Warum Sie|$)",
            r"(?:Basierend auf .*?, hier ist was ich für .*?[Kk]ompetenzen.*?eintrage:\s*)(.*?)(?=\n\n|Warum Sie|$)",
        ]
        
        patterns_fit = [
            r"(?:Warum Sie gut geeignet sind:\s*)(.*?)(?=$|\n\n)",
            r"(?:Ich werde für .*?[Gg]eeignet.*?eintragen:\s*)(.*?)(?=$|\n\n)",
            r"(?:Basierend auf .*?, hier ist was ich für .*?[Ee]ignung.*?eintrage:\s*)(.*?)(?=$|\n\n)",
        ]
    else:
        # English patterns
        patterns_skills = [
            r"(?:Key Skills(?:\s*&\s*Experience)?:\s*)(.*?)(?=Why You're|$)",
            r"(?:I'll put for .*?[Kk]ey [Ss]kills.*?:\s*)(.*?)(?=\n\n|Why You're|$)",
            r"(?:Based on .*?, here's what I'll put for .*?[Ss]kills.*?:\s*)(.*?)(?=\n\n|Why You're|$)",
        ]
        
        patterns_fit = [
            r"(?:Why You're a Good Fit:\s*)(.*?)(?=$|\n\n)",
            r"(?:I'll put for .*?[Gg]ood [Ff]it.*?:\s*)(.*?)(?=$|\n\n)",
            r"(?:Based on .*?, here's what I'll put for .*?[Ff]it.*?:\s*)(.*?)(?=$|\n\n)",
        ]
    
    for pattern in patterns_skills:
        match = re.search(pattern, message, re.IGNORECASE | re.DOTALL)
        if match:
            content = clean_text(match.group(1))
            # Remove any leading explanatory text
            if language == "de":
                content = re.sub(r'^(Hier ist was ich.*?:|Ich werde eintragen:|Basierend auf.*?:)\s*', '', content, flags=re.IGNORECASE)
            else:
                content = re.sub(r'^(Here\'s what I.*?:|I\'ll put:|Based on.*?:)\s*', '', content, flags=re.IGNORECASE)
            if content and len(content) > 20:  # Ensure meaningful content
                field_updates["key_skills"] = content
                break
    
    for pattern in patterns_fit:
        match = re.search(pattern, message, re.IGNORECASE | re.DOTALL)
        if match:
            content = clean_text(match.group(1))
            # Remove any leading explanatory text
            if language == "de":
                content = re.sub(r'^(Hier ist was ich.*?:|Ich werde eintragen:|Basierend auf.*?:)\s*', '', content, flags=re.IGNORECASE)
            else:
                content = re.sub(r'^(Here\'s what I.*?:|I\'ll put:|Based on.*?:)\s*', '', content, flags=re.IGNORECASE)
            if content and len(content) > 20:  # Ensure meaningful content
                field_updates["personal_statement"] = content
                break
    
    # Fallback: Look for content between clear markers
    if "key_skills" not in field_updates:
        # Look for content after phrases like "For your Key Skills section:"
        match = re.search(r"(?:For (?:your |the )?Key Skills.*?:)\s*\"?([^\"]+)\"?", message, re.IGNORECASE)
        if match:
            field_updates["key_skills"] = clean_text(match.group(1))
    
    if "personal_statement" not in field_updates:
        # Look for content after phrases like "For Why You're a Good Fit:"
        match = re.search(r"(?:For (?:your |the )?(?:Why You're a Good Fit|personal statement).*?:)\s*\"?([^\"]+)\"?", message, re.IGNORECASE)
        if match:
            field_updates["personal_statement"] = clean_text(match.group(1))
    
    return field_updates

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time application updates"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep the connection alive and handle any incoming messages
            data = await websocket.receive_text()
            
            # Echo back or handle commands if needed
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        await manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        await manager.disconnect(session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=BACKEND_PORT)