#!/usr/bin/env python3
"""
MCP Server for Internal Job Board Application with ElevenLabs compatibility
Provides both SSE and synchronous endpoints
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from mcp.server import FastMCP
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server for SSE support
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

# Define the tools
@mcp.tool()
async def get_job_details(job_id: str) -> Dict[str, Any]:
    """
    Get details about an internal position to provide context for the conversation.
    
    Args:
        job_id: The ID of the internal position
    
    Returns:
        Dict with job details including title, department, and requirements
    """
    job_data = {
        "id": job_id,
        "title": "Senior Project Manager",
        "department": "Operations",
        "description": "Lead cross-functional teams to deliver strategic initiatives across the organization.",
        "requirements": "Project management experience, stakeholder management skills, analytical mindset",
        "location": "Main Campus - Building A",
        "growth_path": "This role offers leadership development and exposure to executive stakeholders"
    }
    
    return {
        "success": True,
        "job": job_data,
        "message": "I've reviewed the position details. This looks like an exciting opportunity!"
    }

@mcp.tool()
async def update_application_field(
    session_id: str,
    field_name: str,
    value: str
) -> Dict[str, Any]:
    """
    Update a specific field in the job application form in real-time.
    
    Args:
        session_id: The session ID for this application
        field_name: The field to update (name, email, phone, experience, skills, motivation)
        value: The value to set for the field
    
    Returns:
        Dict with success status and encouraging feedback
    """
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
    return {
        "success": True,
        "message": "Congratulations! Your application has been submitted successfully.",
        "application_id": f"{job_id}-{session_id[:8]}",
        "next_steps": "You'll receive an email confirmation shortly."
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
        "nervous": "It's completely natural to feel nervous about internal moves.",
        "unsure": "It's okay to explore opportunities even if you're not 100% sure.",
        "excited": "Your enthusiasm is wonderful!",
        "general": "You're doing great! Remember, applying for internal positions shows initiative."
    }
    
    return {
        "success": True,
        "message": encouragements.get(context, encouragements["general"]),
        "context": context
    }

# Create FastAPI app for additional endpoints
app = FastAPI()

# Mount the SSE app at /sse
sse_app = mcp.sse_app()
app.mount("/sse", sse_app)

# Add synchronous endpoint for ElevenLabs compatibility
@app.post("/")
async def handle_mcp_request(request: Dict[str, Any]):
    """Handle MCP requests in a synchronous manner for ElevenLabs compatibility"""
    method = request.get("method")
    request_id = request.get("id", 1)
    
    logger.info(f"Received request: method={method}, id={request_id}")
    
    # Handle initialize request
    if method == "initialize":
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "internal-mobility-assistant",
                    "version": "1.0.0"
                }
            }
        }
        logger.info("Sent initialize response")
        return JSONResponse(content=response)
    
    # Handle tools/list request
    elif method == "tools/list":
        tools = [
            {
                "name": "get_job_details",
                "description": "Get details about an internal position",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "The ID of the internal position"}
                    },
                    "required": ["job_id"]
                }
            },
            {
                "name": "update_application_field",
                "description": "Update a specific field in the job application form",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "The session ID"},
                        "field_name": {"type": "string", "description": "The field to update"},
                        "value": {"type": "string", "description": "The value to set"}
                    },
                    "required": ["session_id", "field_name", "value"]
                }
            },
            {
                "name": "submit_application",
                "description": "Submit the completed application",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "The session ID"},
                        "job_id": {"type": "string", "description": "The job ID"}
                    },
                    "required": ["session_id", "job_id"]
                }
            },
            {
                "name": "get_encouragement",
                "description": "Provide contextual encouragement",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "context": {"type": "string", "description": "The context for encouragement"}
                    }
                }
            }
        ]
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
        logger.info(f"Sent tools/list response with {len(tools)} tools")
        return JSONResponse(content=response)
    
    # Handle other requests
    else:
        logger.warning(f"Unsupported method: {method}")
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            },
            status_code=404
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "internal-mobility-mcp"}

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000  # Internal port in Docker container
    
    logger.info(f"Starting ElevenLabs-compatible MCP server on {host}:{port}")
    logger.info(f"SSE endpoint: http://{host}:{port}/sse")
    logger.info(f"Synchronous endpoint: http://{host}:{port}/")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )