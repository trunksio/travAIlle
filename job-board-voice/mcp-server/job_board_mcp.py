#!/usr/bin/env python3
"""
MCP Server for Internal Job Board Application
Based on working VW SSE server example
"""

import os
import json
import logging
import time
from typing import Dict, Any
from datetime import datetime

# Set up logging with debug level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from mcp.server import FastMCP

# Import Redis if available
try:
    import redis
    REDIS_AVAILABLE = True
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    logger.info(f"Redis connected at {REDIS_URL}")
except ImportError:
    logger.warning("Redis not available. Using in-memory storage.")
    REDIS_AVAILABLE = False
    redis_client = None
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
    REDIS_AVAILABLE = False
    redis_client = None

# In-memory storage as fallback
memory_store = {}

# Create FastMCP server with supportive instructions
mcp = FastMCP(
    name="internal-mobility-assistant",
    instructions="""You are a supportive AI career coach helping employees explore internal opportunities within their organization.

Your role is to:
1. Help employees articulate their transferable skills and experience
2. Reduce anxiety about applying for internal positions
3. Encourage professional growth and career development
4. Guide them through the application process with warmth and professionalism

Be warm, encouraging, and professional. Help them recognize their value and potential.
Remember that they already work for the company, so focus on their growth journey and transferable skills.

When they share information:
- Use update_application_field to save their responses in real-time
- Always be positive and help them see their strengths
- Provide encouragement and constructive feedback

Start by asking about the position they're interested in and what excites them about it."""
)

@mcp.tool()
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """
    Get details about an internal position to provide context for the conversation.
    
    Args:
        job_id: The ID of the internal position
    
    Returns:
        Dict with job details including title, department, and requirements
    """
    try:
        if REDIS_AVAILABLE and redis_client:
            try:
                job_data = redis_client.hgetall(f"job:{job_id}")
            except:
                job_data = {}
        else:
            job_data = {}
        
        if not job_data:
            # Return a default internal position for demo
            job_data = {
                "id": job_id,
                "title": "Senior Project Manager",
                "department": "Operations",
                "description": "Lead cross-functional teams to deliver strategic initiatives across the organization.",
                "requirements": "Project management experience, stakeholder management skills, analytical mindset",
                "location": "Main Campus - Building A",
                "growth_path": "This role offers leadership development and exposure to executive stakeholders"
            }
        
        logger.info(f"Retrieved details for position {job_id}")
        
        return {
            "success": True,
            "job": job_data,
            "message": "I've reviewed the position details. This looks like an exciting opportunity! What aspects of this role appeal most to you?"
        }
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        return {
            "success": False,
            "error": str(e),
            "job": {
                "title": "Position",
                "department": "Unknown"
            }
        }

@mcp.tool()
async def update_application_field(
    session_id: str,
    field_name: str,
    value: str
) -> Dict[str, Any]:
    """
    Update a specific field in the job application form in real-time.
    This tool is called as the candidate provides information during the voice interview.
    
    Args:
        session_id: The session ID for this application
        field_name: The field to update (name, email, phone, experience, skills, motivation)
        value: The value to set for the field
    
    Returns:
        Dict with success status and encouraging feedback
    """
    try:
        # Store the field update
        if REDIS_AVAILABLE and redis_client:
            try:
                key = f"application:{session_id}"
                redis_client.hset(key, field_name, value)
                redis_client.hset(key, f"{field_name}_updated_at", datetime.now().isoformat())
                redis_client.expire(key, 3600)  # Expire after 1 hour
                
                # Publish update for real-time form update
                update_message = json.dumps({
                    "type": "field_update",
                    "session_id": session_id,
                    "field_name": field_name,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                })
                redis_client.publish(f"application_updates:{session_id}", update_message)
            except Exception as e:
                logger.warning(f"Redis operation failed: {e}, using memory")
                if session_id not in memory_store:
                    memory_store[session_id] = {}
                memory_store[session_id][field_name] = value
        else:
            # Store in memory
            if session_id not in memory_store:
                memory_store[session_id] = {}
            memory_store[session_id][field_name] = value
        
        logger.info(f"Updated field {field_name} for session {session_id}")
        
        # Provide encouraging feedback based on the field
        encouragement = {
            "name": "Thank you! It's great to connect with you.",
            "email": "Perfect, I've noted your contact information.",
            "phone": "Got it, thank you for providing that.",
            "experience": "That's excellent experience! Your background really aligns well with this role.",
            "skills": "Those are impressive skills! They'll definitely be valuable in this position.",
            "motivation": "I can really feel your enthusiasm! Your passion for this role comes through clearly.",
            "cover_letter": "That's a compelling statement! You've articulated your value very well."
        }
        
        return {
            "success": True,
            "field_name": field_name,
            "message": encouragement.get(field_name, "Thank you for sharing that with me!"),
            "value": value[:100] + "..." if len(value) > 100 else value
        }
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        return {
            "success": False,
            "error": str(e),
            "field_name": field_name
        }

@mcp.tool()
async def submit_application(
    session_id: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Submit the completed application for the internal position.
    
    Args:
        session_id: The session ID for this application
        job_id: The ID of the job being applied for
    
    Returns:
        Dict with submission confirmation and next steps
    """
    try:
        # Mark application as submitted
        if REDIS_AVAILABLE and redis_client:
            try:
                key = f"application:{session_id}"
                redis_client.hset(key, "status", "submitted")
                redis_client.hset(key, "job_id", job_id)
                redis_client.hset(key, "submitted_at", datetime.now().isoformat())
                
                # Get all application data
                application_data = redis_client.hgetall(key)
                
                # Store in submitted applications
                submission_key = f"submission:{job_id}:{session_id}"
                redis_client.hmset(submission_key, application_data)
                redis_client.expire(submission_key, 86400 * 7)  # Keep for 7 days
            except:
                if session_id in memory_store:
                    memory_store[session_id]["status"] = "submitted"
                    memory_store[session_id]["job_id"] = job_id
        else:
            if session_id in memory_store:
                memory_store[session_id]["status"] = "submitted"
                memory_store[session_id]["job_id"] = job_id
        
        logger.info(f"Submitted application {session_id} for job {job_id}")
        
        return {
            "success": True,
            "message": "Congratulations! Your application has been submitted successfully. You've taken an important step in your career journey. The hiring team will review your application and reach out soon. Best of luck!",
            "application_id": f"{job_id}-{session_id[:8]}",
            "next_steps": "You'll receive an email confirmation shortly. The hiring manager typically responds within 3-5 business days."
        }
    except Exception as e:
        logger.error(f"Error submitting application: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "There was an issue submitting your application, but don't worry - your responses have been saved. Please try again or contact HR for assistance."
        }

@mcp.tool()
async def get_encouragement(context: str = "general") -> Dict[str, Any]:
    """
    Provide contextual encouragement during the application process.
    
    Args:
        context: The context for encouragement (e.g., "nervous", "unsure", "excited")
    
    Returns:
        Dict with encouraging message
    """
    encouragements = {
        "nervous": "It's completely natural to feel nervous about internal moves. Remember, your company values your growth and wants to see you succeed. You already know the culture and have proven yourself here.",
        "unsure": "It's okay to explore opportunities even if you're not 100% sure. This conversation is about discovering if this role aligns with your goals. There's no pressure - just be yourself.",
        "excited": "Your enthusiasm is wonderful! That positive energy will really come through in your application. Let's channel that excitement into showcasing your strengths.",
        "general": "You're doing great! Remember, applying for internal positions shows initiative and ambition. Your company wants to retain talented people like you.",
        "experience": "Every role you've had has given you valuable skills. Even experiences that seem unrelated often provide transferable skills that are highly valuable.",
        "skills": "Don't underestimate your abilities. The skills you use daily in your current role are valuable assets. Let's identify how they apply to this new opportunity."
    }
    
    return {
        "success": True,
        "message": encouragements.get(context, encouragements["general"]),
        "context": context
    }

# Create the ASGI app for SSE
app = mcp.sse_app()

if __name__ == "__main__":
    import sys
    import uvicorn
    
    # Check transport mode
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    if transport == "stdio" or "--transport" in sys.argv and "stdio" in sys.argv:
        # Run in stdio mode for local development
        logger.info("Starting Job Board MCP server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        # Run in SSE mode for production
        host = "0.0.0.0"
        port = 8000  # Internal port in Docker container
        
        logger.info(f"Starting Job Board MCP server in SSE mode on {host}:{port}")
        logger.info(f"SSE endpoint will be available at http://{host}:{port}/sse")
        
        # Run with uvicorn like the working example
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="debug"
        )