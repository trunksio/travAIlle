#!/usr/bin/env python3
"""
MCP Server for Internal Job Mobility Platform
Provides supportive tools for employees applying to internal positions
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastmcp import FastMCP

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
4. Guide them through two key questions:
   - "What key skills and experience do you bring to this role?"
   - "Why do you feel you're a good fit for this position?"

Be warm, encouraging, and professional. Help them recognize their value and potential.
Remember that they already work for the company, so focus on their growth journey and transferable skills.

When they share their thoughts:
- Use submit_key_skills to save their skills and experience
- Use submit_personal_statement to save their personal statement
- Always be positive and help them see their strengths

Start by using get_job_details to understand the role they're interested in."""
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
            job_data = redis_client.hgetall(f"job:{job_id}")
        else:
            job_data = {}
        
        if not job_data:
            # Return a default internal position for demo
            job_data = {
                "title": "Senior Project Manager",
                "department": "Operations",
                "description": "Lead cross-functional teams to deliver strategic initiatives",
                "requirements": "Project management experience, stakeholder management, analytical skills",
                "location": "Same campus - Building A",
                "growth_path": "This role offers leadership development and exposure to executive stakeholders"
            }
        
        logger.info(f"Retrieved details for position {job_id}")
        
        return {
            "success": True,
            "job": job_data,
            "message": "I've reviewed the position details. Let me help you articulate your fit for this role."
        }
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def submit_key_skills(session_id: str, skills_text: str) -> Dict[str, Any]:
    """
    Save the employee's key skills and experience for the application.
    
    Args:
        session_id: The session ID for this application
        skills_text: The employee's articulated skills and experience
    
    Returns:
        Dict with success status and encouraging message
    """
    try:
        if REDIS_AVAILABLE and redis_client:
            # Store in Redis
            key = f"application:{session_id}"
            redis_client.hset(key, "key_skills", skills_text)
            redis_client.hset(key, "skills_updated_at", datetime.now().isoformat())
            redis_client.expire(key, 3600)
            
            # Publish update for real-time form update
            update_message = json.dumps({
                "type": "field_update",
                "session_id": session_id,
                "field_name": "key_skills",
                "value": skills_text,
                "timestamp": datetime.now().isoformat()
            })
            redis_client.publish(f"application_updates:{session_id}", update_message)
        else:
            # Store in memory
            if session_id not in memory_store:
                memory_store[session_id] = {}
            memory_store[session_id]["key_skills"] = skills_text
        
        logger.info(f"Updated key skills for session {session_id}")
        
        return {
            "success": True,
            "field_name": "key_skills",
            "message": "Excellent! I've captured your skills and experience. These really highlight your capabilities for this role."
        }
    except Exception as e:
        logger.error(f"Error updating key skills: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def submit_personal_statement(session_id: str, statement_text: str) -> Dict[str, Any]:
    """
    Save the employee's personal statement about why they're a good fit.
    
    Args:
        session_id: The session ID for this application
        statement_text: The employee's personal statement
    
    Returns:
        Dict with success status and encouraging message
    """
    try:
        if REDIS_AVAILABLE and redis_client:
            # Store in Redis
            key = f"application:{session_id}"
            redis_client.hset(key, "personal_statement", statement_text)
            redis_client.hset(key, "statement_updated_at", datetime.now().isoformat())
            redis_client.expire(key, 3600)
            
            # Publish update for real-time form update
            update_message = json.dumps({
                "type": "field_update",
                "session_id": session_id,
                "field_name": "personal_statement",
                "value": statement_text,
                "timestamp": datetime.now().isoformat()
            })
            redis_client.publish(f"application_updates:{session_id}", update_message)
            
            # Mark application as ready
            redis_client.hset(key, "ai_assisted_complete", "true")
        else:
            # Store in memory
            if session_id not in memory_store:
                memory_store[session_id] = {}
            memory_store[session_id]["personal_statement"] = statement_text
            memory_store[session_id]["ai_assisted_complete"] = True
        
        logger.info(f"Updated personal statement for session {session_id}")
        
        return {
            "success": True,
            "field_name": "personal_statement",
            "message": "Perfect! Your personal statement really shows your enthusiasm and fit for this role. You're ready to complete your application!"
        }
    except Exception as e:
        logger.error(f"Error updating personal statement: {e}")
        return {"success": False, "error": str(e)}

# Create the ASGI app for SSE
app = mcp.sse_app()

if __name__ == "__main__":
    import sys
    import uvicorn
    
    # Check transport mode
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    if transport == "stdio" or "--transport" in sys.argv and "stdio" in sys.argv:
        # Run in stdio mode for local development
        logger.info("Starting Internal Mobility MCP server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        # Run in SSE mode for production
        host = "0.0.0.0"
        port = 8000  # Internal port in Docker container
        
        logger.info(f"Starting Internal Mobility MCP server in SSE mode on {host}:{port}")
        logger.info(f"SSE endpoint will be available at http://{host}:{port}/sse")
        
        # Run with uvicorn like the working example
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info"
        )