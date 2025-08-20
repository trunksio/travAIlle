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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))

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
    department: str
    description: str
    requirements: str
    location: str
    growth_path: str
    posted_date: str
    team_size: Optional[str] = None

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
            "department": "Operations",
            "description": "Lead cross-functional teams to deliver strategic initiatives across the organization. This role offers exposure to executive leadership and the opportunity to shape our operational excellence.",
            "requirements": "Experience in project management, strong stakeholder management skills, analytical mindset, ability to manage multiple priorities",
            "location": "Main Campus - Building A",
            "growth_path": "Leadership track with potential progression to Director of Operations",
            "posted_date": datetime.now().isoformat(),
            "team_size": "12-15 team members"
        },
        {
            "id": "job_002",
            "title": "Lead Data Analyst",
            "department": "Finance",
            "description": "Join our Finance team to drive data-driven decision making. You'll work directly with CFO leadership to provide insights that shape our financial strategy.",
            "requirements": "Strong analytical skills, experience with financial modeling, proficiency in data visualization tools, understanding of business metrics",
            "location": "Main Campus - Building B",
            "growth_path": "Analytics leadership path with exposure to strategic planning",
            "posted_date": datetime.now().isoformat(),
            "team_size": "5-7 team members"
        },
        {
            "id": "job_003",
            "title": "Product Owner",
            "department": "Digital Innovation",
            "description": "Drive the product vision for our internal digital transformation initiatives. You'll collaborate with IT and business units to modernize our employee experience.",
            "requirements": "Product management mindset, understanding of agile methodologies, ability to translate business needs to technical requirements, strong communication skills",
            "location": "Tech Hub - Flexible",
            "growth_path": "Product leadership with opportunity to shape digital strategy",
            "posted_date": datetime.now().isoformat(),
            "team_size": "8-10 team members"
        },
        {
            "id": "job_004",
            "title": "Team Lead - Customer Success",
            "department": "Customer Experience",
            "description": "Lead a team dedicated to ensuring customer satisfaction and retention. This people-focused role combines leadership with hands-on customer engagement.",
            "requirements": "Leadership experience or potential, customer-centric mindset, problem-solving skills, ability to mentor and develop others",
            "location": "Any Regional Office",
            "growth_path": "Management track with path to Head of Customer Success",
            "posted_date": datetime.now().isoformat(),
            "team_size": "8-12 team members"
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