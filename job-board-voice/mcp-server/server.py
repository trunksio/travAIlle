"""
MCP Server for Job Board Application
Provides tools for updating application forms in real-time
"""

import os
import json
import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

import redis.asyncio as redis
from mcp.server import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create MCP server with SSE support
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

class ApplicationField(BaseModel):
    """Model for updating a single application field"""
    session_id: str = Field(description="Session ID for the application")
    field_name: str = Field(description="Name of the field to update (name, email, phone, experience, skills)")
    value: str = Field(description="Value to set for the field")

class ApplicationSubmission(BaseModel):
    """Model for submitting the complete application"""
    session_id: str = Field(description="Session ID for the application")
    job_id: str = Field(description="ID of the job being applied for")

async def get_redis_client():
    """Get Redis client connection"""
    return await redis.from_url(REDIS_URL, decode_responses=True)

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
        field_name: The field to update (name, email, phone, years_experience, skills, cover_letter)
        value: The value to set for the field
    
    Returns:
        Dict with success status and updated field information
    """
    try:
        client = await get_redis_client()
        
        # Store the field update
        key = f"application:{session_id}"
        field_key = f"{field_name}"
        
        # Update the field
        await client.hset(key, field_key, value)
        await client.expire(key, 3600)  # Expire after 1 hour
        
        # Publish update for real-time notification
        update_message = json.dumps({
            "type": "field_update",
            "session_id": session_id,
            "field_name": field_name,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        await client.publish(f"application_updates:{session_id}", update_message)
        
        logger.info(f"Updated field {field_name} for session {session_id}")
        
        await client.close()
        
        return {
            "success": True,
            "field_name": field_name,
            "value": value,
            "message": f"Updated {field_name} successfully"
        }
    except Exception as e:
        logger.error(f"Error updating application field: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """
    Get details about a specific job posting to provide context during the interview.
    
    Args:
        job_id: The ID of the job to retrieve
    
    Returns:
        Dict with job details including title, description, and requirements
    """
    try:
        client = await get_redis_client()
        
        # Get job details from Redis
        job_data = await client.hgetall(f"job:{job_id}")
        
        if not job_data:
            # Return a default job if not found (for demo purposes)
            job_data = {
                "title": "Software Engineer",
                "company": "TechCorp",
                "description": "We're looking for a talented software engineer to join our team.",
                "requirements": "3+ years experience, Python, JavaScript, API development",
                "location": "Remote",
                "salary_range": "$100,000 - $150,000"
            }
        
        await client.close()
        
        return {
            "success": True,
            "job": job_data
        }
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def submit_application(
    session_id: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Submit the completed job application after all fields have been filled.
    
    Args:
        session_id: The session ID for this application
        job_id: The ID of the job being applied for
    
    Returns:
        Dict with submission status and application ID
    """
    try:
        client = await get_redis_client()
        
        # Get all application data
        app_data = await client.hgetall(f"application:{session_id}")
        
        if not app_data:
            return {
                "success": False,
                "error": "No application data found for this session"
            }
        
        # Validate required fields
        required_fields = ["name", "email", "phone"]
        missing_fields = [f for f in required_fields if f not in app_data]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }
        
        # Create application record
        app_id = f"app_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        app_data["job_id"] = job_id
        app_data["application_id"] = app_id
        app_data["submitted_at"] = datetime.now().isoformat()
        app_data["status"] = "submitted"
        
        # Store the application
        await client.hset(f"submitted_application:{app_id}", mapping=app_data)
        
        # Add to job's application list
        await client.lpush(f"job_applications:{job_id}", app_id)
        
        # Publish submission event
        submission_message = json.dumps({
            "type": "application_submitted",
            "session_id": session_id,
            "application_id": app_id,
            "job_id": job_id,
            "timestamp": datetime.now().isoformat()
        })
        await client.publish(f"application_updates:{session_id}", submission_message)
        
        # Clean up temporary application data
        await client.delete(f"application:{session_id}")
        
        logger.info(f"Submitted application {app_id} for job {job_id}")
        
        await client.close()
        
        return {
            "success": True,
            "application_id": app_id,
            "message": "Application submitted successfully!"
        }
    except Exception as e:
        logger.error(f"Error submitting application: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_application_status(session_id: str) -> Dict[str, Any]:
    """
    Get the current status of an application form to understand what fields have been filled.
    
    Args:
        session_id: The session ID for this application
    
    Returns:
        Dict with current application data and completion status
    """
    try:
        client = await get_redis_client()
        
        # Get current application data
        app_data = await client.hgetall(f"application:{session_id}")
        
        # Check which required fields are complete
        required_fields = ["name", "email", "phone"]
        optional_fields = ["years_experience", "skills", "cover_letter"]
        
        filled_required = [f for f in required_fields if f in app_data]
        filled_optional = [f for f in optional_fields if f in app_data]
        missing_required = [f for f in required_fields if f not in app_data]
        
        completion_percentage = (len(filled_required) / len(required_fields)) * 100
        
        await client.close()
        
        return {
            "success": True,
            "session_id": session_id,
            "filled_fields": {
                "required": filled_required,
                "optional": filled_optional
            },
            "missing_required": missing_required,
            "completion_percentage": completion_percentage,
            "current_data": app_data,
            "ready_to_submit": len(missing_required) == 0
        }
    except Exception as e:
        logger.error(f"Error getting application status: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import sys
    import uvicorn
    
    # Check transport mode
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    if transport == "stdio" or "--transport" in sys.argv and "stdio" in sys.argv:
        # Run in stdio mode for local development
        logger.info("Starting MCP server in stdio mode...")
        mcp.run(transport="stdio")
    else:
        # Run in SSE mode for production
        host = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_SERVER_PORT", 3000))
        logger.info(f"Starting MCP server in SSE mode on {host}:{port}")
        # For FastMCP with SSE, we need to run it differently
        mcp.run(transport="sse", sse_server_host=host, sse_server_port=port)