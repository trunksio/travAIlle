#!/usr/bin/env python3
"""
Working MCP Server for Job Board Application using FastMCP
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

# Create FastMCP server
mcp = FastMCP(
    name="job-board-mcp",
    instructions="""You are an AI assistant helping candidates apply for jobs through voice interaction.
    
    When conducting the interview:
    1. Start by introducing yourself and the position they're applying for
    2. Ask for their information progressively (name, email, phone, experience, skills)
    3. Use the update_application_field tool to update form fields in real-time as they provide information
    4. Confirm the information before final submission
    5. Use submit_application when all required fields are complete
    
    Be conversational and encouraging, helping candidates present their best qualifications."""
)

@mcp.tool()
async def update_application_field(session_id: str, field_name: str, value: str) -> Dict[str, Any]:
    """Update a specific field in the job application form"""
    try:
        if REDIS_AVAILABLE and redis_client:
            # Store in Redis
            key = f"application:{session_id}"
            redis_client.hset(key, field_name, value)
            redis_client.expire(key, 3600)
            
            # Publish update
            update_message = json.dumps({
                "type": "field_update",
                "session_id": session_id,
                "field_name": field_name,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
            redis_client.publish(f"application_updates:{session_id}", update_message)
        else:
            # Store in memory
            if session_id not in memory_store:
                memory_store[session_id] = {}
            memory_store[session_id][field_name] = value
        
        logger.info(f"Updated {field_name} for session {session_id}")
        
        return {
            "success": True,
            "field_name": field_name,
            "value": value,
            "message": f"Updated {field_name} successfully"
        }
    except Exception as e:
        logger.error(f"Error updating field: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """Get details about a specific job posting"""
    try:
        if REDIS_AVAILABLE and redis_client:
            job_data = redis_client.hgetall(f"job:{job_id}")
        else:
            job_data = {}
        
        if not job_data:
            # Return default job for demo
            job_data = {
                "title": "Software Engineer",
                "company": "TechCorp",
                "description": "Join our innovative team",
                "requirements": "3+ years experience",
                "location": "Remote",
                "salary_range": "$100k-$150k"
            }
        
        return {"success": True, "job": job_data}
    except Exception as e:
        logger.error(f"Error getting job: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def submit_application(session_id: str, job_id: str) -> Dict[str, Any]:
    """Submit the completed job application"""
    try:
        if REDIS_AVAILABLE and redis_client:
            app_data = redis_client.hgetall(f"application:{session_id}")
        else:
            app_data = memory_store.get(session_id, {})
        
        if not app_data:
            return {"success": False, "error": "No application data found"}
        
        # Check required fields
        required = ["name", "email", "phone"]
        missing = [f for f in required if f not in app_data]
        
        if missing:
            return {
                "success": False,
                "error": f"Missing fields: {', '.join(missing)}",
                "missing_fields": missing
            }
        
        # Create application ID
        app_id = f"app_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if REDIS_AVAILABLE and redis_client:
            # Store application
            app_data["job_id"] = job_id
            app_data["application_id"] = app_id
            app_data["submitted_at"] = datetime.now().isoformat()
            redis_client.hset(f"submitted_application:{app_id}", mapping=app_data)
            redis_client.lpush(f"job_applications:{job_id}", app_id)
            
            # Publish submission event
            submission_message = json.dumps({
                "type": "application_submitted",
                "session_id": session_id,
                "application_id": app_id,
                "job_id": job_id,
                "timestamp": datetime.now().isoformat()
            })
            redis_client.publish(f"application_updates:{session_id}", submission_message)
            
            # Clean up
            redis_client.delete(f"application:{session_id}")
        
        logger.info(f"Submitted application {app_id}")
        
        return {
            "success": True,
            "application_id": app_id,
            "message": "Application submitted successfully!"
        }
    except Exception as e:
        logger.error(f"Error submitting: {e}")
        return {"success": False, "error": str(e)}

@mcp.tool()
async def get_application_status(session_id: str) -> Dict[str, Any]:
    """Get the current status of an application form"""
    try:
        if REDIS_AVAILABLE and redis_client:
            app_data = redis_client.hgetall(f"application:{session_id}")
        else:
            app_data = memory_store.get(session_id, {})
        
        required = ["name", "email", "phone"]
        filled_required = [f for f in required if f in app_data]
        missing_required = [f for f in required if f not in app_data]
        
        completion = (len(filled_required) / len(required)) * 100 if required else 0
        
        return {
            "success": True,
            "session_id": session_id,
            "filled_fields": list(app_data.keys()),
            "missing_required": missing_required,
            "completion_percentage": completion,
            "current_data": app_data,
            "ready_to_submit": len(missing_required) == 0
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import sys
    
    # Check transport mode
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    if transport == "stdio" or "--transport" in sys.argv and "stdio" in sys.argv:
        # Run in stdio mode for local development
        logger.info("Starting MCP server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        # Run in SSE mode for production
        # FastMCP uses port 8000 internally by default
        logger.info(f"Starting MCP server in SSE mode")
        # The server will run on port 8000 internally, mapped to 3000 externally via Docker
        mcp.run(transport="sse")