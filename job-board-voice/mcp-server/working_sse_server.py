#!/usr/bin/env python3
"""
VW Customer Support MCP Server with SSE Support
Based on FastMCP for proper SSE implementation
"""

import asyncio
import logging
import time
from typing import Dict, Any

from mcp.server import FastMCP
from pydantic import BaseModel

# Add parent directory to path for imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.tools.location_search import LocationSearchTool
from src.tools.parts_lookup import PartsLookupTool
from src.tools.supervisor_ui import SupervisorUITool
from src.tools.whatsapp_sender import WhatsAppSenderTool
from src.tools.sms_sender import SMSSenderTool
from src.tools.test_drive_manager import TestDriveManager
from src.utils.tool_logger import tool_logger

# Decorator for logging tool calls
from functools import wraps

def log_tool_call(tool_name: str):
    """Decorator to log MCP tool calls"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            error_msg = None
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful call
                duration_ms = (time.time() - start_time) * 1000
                await tool_logger.log_tool_call(
                    tool_name=tool_name,
                    arguments=kwargs,
                    result=result,
                    duration_ms=duration_ms
                )
                
                return result
            except Exception as e:
                error_msg = str(e)
                
                # Create error response
                result = {"error": error_msg}
                
                # Log failed call
                duration_ms = (time.time() - start_time) * 1000
                await tool_logger.log_tool_call(
                    tool_name=tool_name,
                    arguments=kwargs,
                    result=result,
                    error=error_msg,
                    duration_ms=duration_ms
                )
                
                raise
        return wrapper
    return decorator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP(
    name="vw-customer-support",
    instructions="""VW Customer Support MCP Server
    
    This server provides tools for Volkswagen customer support operations:
    - Search for VW service centers by location
    - Look up compatible parts by vehicle registration
    - Escalate complex issues to human supervisors
    - Send information to customers via WhatsApp messaging
    """
)

# Initialize tools as singletons
settings = Settings()
location_tool = LocationSearchTool(settings)
parts_tool = PartsLookupTool(settings)
supervisor_tool = SupervisorUITool(settings)
whatsapp_tool = WhatsAppSenderTool(settings)
sms_tool = SMSSenderTool(settings)
test_drive_manager = TestDriveManager(settings)


@mcp.tool()
async def find_service_centers(location: str, radius_km: float = 25, language: str = "en") -> dict:
    """
    Search for Volkswagen authorized service centers and dealerships within a specified radius of a location.
    Returns contact details, ratings, and available services.
    
    LOCALIZATION NOTE: Pass language="de" for German (distances in km, German terminology)
    or language="en" for English (distances in miles, UK spelling like 'tyre' not 'tire').
    
    Args:
        location: Address, city, or coordinates to search near
        radius_km: Search radius in kilometers (will be displayed in miles for English)
        language: Language code for localization - "en" for English (miles, UK spelling) or "de" for German (km)
    
    Returns:
        Dictionary containing service centers found with localized distances and terminology
    """
    start_time = time.time()
    error_msg = None
    
    try:
        logger.info(f"Searching for service centers near {location} within {radius_km}km")
        result = await location_tool.search_service_centers(
            location=location,
            radius_km=radius_km,
            language=language
        )
        
        response = {
            "service_centers": result.get("service_centers", []),
            "search_location": location,
            "radius_km": radius_km,
            "radius": result.get("radius"),
            "radius_unit": result.get("radius_unit"),
            "count": len(result.get("service_centers", [])),
            "language": language
        }
        
        # Log successful call
        duration_ms = (time.time() - start_time) * 1000
        await tool_logger.log_tool_call(
            tool_name="find_service_centers",
            arguments={"location": location, "radius_km": radius_km, "language": language},
            result=response,
            duration_ms=duration_ms
        )
        
        return response
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error searching service centers: {error_msg}")
        
        response = {
            "error": error_msg,
            "service_centers": [],
            "search_location": location,
            "radius_km": radius_km
        }
        
        # Log failed call
        duration_ms = (time.time() - start_time) * 1000
        await tool_logger.log_tool_call(
            tool_name="find_service_centers",
            arguments={"location": location, "radius_km": radius_km, "language": language},
            result=response,
            error=error_msg,
            duration_ms=duration_ms
        )
        
        return response


@mcp.tool()
async def lookup_parts(registration_plate: str, part_category: str = "all", language: str = "en") -> dict:
    """
    Retrieve OEM and compatible replacement parts for a specific VW vehicle using its registration plate.
    Returns part numbers, prices, and availability.
    
    LOCALIZATION NOTE: Pass language="de" for German part names or language="en" for English
    with UK terminology (e.g., 'tyre' not 'tire', 'bonnet' not 'hood').
    
    Args:
        registration_plate: Vehicle registration number
        part_category: Filter by category (e.g., engine, brakes, filters) - default: "all"
        language: Language code for localization - "en" for English (UK terms) or "de" for German
    
    Returns:
        Dictionary containing vehicle info and compatible parts with localized names
    """
    try:
        logger.info(f"Looking up parts for vehicle {registration_plate}, category: {part_category}")
        result = await parts_tool.lookup_parts(
            registration_plate=registration_plate,
            part_category=part_category,
            language=language
        )
        
        return {
            "vehicle": result.get("vehicle", {}),
            "parts": result.get("parts", []),
            "registration_plate": registration_plate,
            "part_category": part_category,
            "parts_count": len(result.get("parts", [])),
            "language": language
        }
    except Exception as e:
        logger.error(f"Error looking up parts: {str(e)}")
        return {
            "error": str(e),
            "vehicle": {},
            "parts": [],
            "registration_plate": registration_plate,
            "part_category": part_category
        }


@mcp.tool()
async def ask_supervisor(question: str, context: dict, priority: str = "medium") -> dict:
    """
    Request human supervisor assistance for complex issues requiring manual review, 
    warranty exceptions, or policy clarifications. Use when automated tools cannot 
    resolve the customer's request.
    
    Args:
        question: The question to ask the supervisor
        context: Conversation context and relevant information
        priority: Priority level - "low", "medium", or "high" (default: "medium")
    
    Returns:
        Dictionary containing supervisor's response
    """
    try:
        # Validate priority
        if priority not in ["low", "medium", "high"]:
            priority = "medium"
        
        logger.info(f"Escalating to supervisor with priority {priority}: {question}")
        result = await supervisor_tool.ask_supervisor(
            question=question,
            context=context,
            priority=priority
        )
        
        return {
            "supervisor_response": result.get("supervisor_response", ""),
            "response_time_seconds": result.get("response_time_seconds", 0),
            "supervisor_id": result.get("supervisor_id", ""),
            "priority": priority,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Error contacting supervisor: {str(e)}")
        return {
            "error": str(e),
            "supervisor_response": f"Unable to contact supervisor: {str(e)}",
            "response_time_seconds": 0,
            "supervisor_id": "",
            "priority": priority,
            "status": "failed"
        }


@mcp.tool()
async def send_whatsapp(to_number: str, message_content: str) -> dict:
    """
    Send information or conversation summary to customer via WhatsApp.
    Uses Twilio API to deliver messages directly to the customer's WhatsApp account.
    
    IMPORTANT: When you have access to system_caller_id in your metadata (e.g., from ElevenLabs),
    you MUST use that as the to_number parameter. The system_caller_id represents the phone number
    of the person who initiated the call and should be the recipient of the WhatsApp message.
    
    Example usage:
    - If system_caller_id is available: send_whatsapp(to_number=system_caller_id, message_content="Your message")
    - If no system_caller_id: send_whatsapp(to_number="+447483245017", message_content="Your message")
    
    Args:
        to_number: Customer's WhatsApp phone number. Use system_caller_id from metadata when available.
        message_content: The message or information to send to the customer
    
    Returns:
        Dictionary containing send status and message details
    """
    start_time = time.time()
    
    try:
        logger.info(f"Sending WhatsApp message to {to_number}")
        result = await whatsapp_tool.send_whatsapp(
            to_number=to_number,
            message_content=message_content,
            caller_id=to_number  # The to_number should be system_caller_id when called by ElevenLabs
        )
        
        # Log the tool call
        duration_ms = (time.time() - start_time) * 1000
        await tool_logger.log_tool_call(
            tool_name="send_whatsapp",
            arguments={"to_number": to_number, "message_content": message_content[:100]},
            result=result,
            error=None if result.get("success") else result.get("error"),
            duration_ms=duration_ms
        )
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending WhatsApp: {error_msg}")
        
        # Log failed call
        duration_ms = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "error": error_msg,
            "to_number": to_number,
            "message_preview": message_content[:100] + "..." if len(message_content) > 100 else message_content
        }
        
        await tool_logger.log_tool_call(
            tool_name="send_whatsapp",
            arguments={"to_number": to_number, "message_content": message_content[:100]},
            result=result,
            error=error_msg,
            duration_ms=duration_ms
        )
        
        return result


@mcp.tool()
async def send_sms(to_number: str, message_content: str) -> dict:
    """
    Send information or conversation summary to customer via SMS (text message).
    Uses Twilio API to deliver messages directly to the customer's mobile phone.
    
    IMPORTANT: When you have access to system_caller_id in your metadata (e.g., from ElevenLabs),
    you MUST use that as the to_number parameter. The system_caller_id represents the phone number
    of the person who initiated the call and should be the recipient of the SMS message.
    
    Example usage:
    - If system_caller_id is available: send_sms(to_number=system_caller_id, message_content="Your message")
    - If no system_caller_id: send_sms(to_number="+447483245017", message_content="Your message")
    
    Args:
        to_number: Customer's mobile phone number. Use system_caller_id from metadata when available.
        message_content: The message or information to send to the customer
    
    Returns:
        Dictionary containing send status and message details including segment count
    """
    start_time = time.time()
    
    try:
        logger.info(f"Sending SMS message to {to_number}")
        result = await sms_tool.send_sms(
            to_number=to_number,
            message_content=message_content,
            caller_id=to_number  # The to_number should be system_caller_id when called by ElevenLabs
        )
        
        # Log the tool call
        duration_ms = (time.time() - start_time) * 1000
        await tool_logger.log_tool_call(
            tool_name="send_sms",
            arguments={"to_number": to_number, "message_content": message_content[:100]},
            result=result,
            error=None if result.get("success") else result.get("error"),
            duration_ms=duration_ms
        )
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending SMS: {error_msg}")
        
        # Log failed call
        duration_ms = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "error": error_msg,
            "to_number": to_number,
            "message_preview": message_content[:160] + "..." if len(message_content) > 160 else message_content
        }
        
        await tool_logger.log_tool_call(
            tool_name="send_sms",
            arguments={"to_number": to_number, "message_content": message_content[:100]},
            result=result,
            error=error_msg,
            duration_ms=duration_ms
        )
        
        return result


@mcp.tool()
async def check_test_drive_availability(date: str) -> dict:
    """
    Check available test drive slots for the VW ID.7 on a specific date.
    Test drives are 1-hour slots available Monday-Saturday, 9am-5pm.
    
    Args:
        date: Date in YYYY-MM-DD format to check for availability
    
    Returns:
        Dictionary containing available 1-hour time slots
    """
    start_time = time.time()
    
    try:
        result = await test_drive_manager.check_availability(date=date)
        
        # Log successful call
        duration_ms = (time.time() - start_time) * 1000
        await tool_logger.log_tool_call(
            tool_name="check_test_drive_availability",
            arguments={"date": date},
            result=result,
            duration_ms=duration_ms
        )
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error checking test drive availability: {error_msg}")
        
        # Log failed call
        duration_ms = (time.time() - start_time) * 1000
        result = {"error": error_msg}
        
        await tool_logger.log_tool_call(
            tool_name="check_test_drive_availability",
            arguments={"date": date},
            result=result,
            error=error_msg,
            duration_ms=duration_ms
        )
        
        return result


@mcp.tool()
async def book_test_drive(
    date: str, 
    time: str,
    customer_phone: str = None,
    customer_name: str = None
) -> dict:
    """
    Book a 1-hour test drive slot for the VW ID.7 electric vehicle.
    
    IMPORTANT: When system_caller_id is available in metadata, use it as customer_phone.
    
    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM format (must be on the hour: 09:00, 10:00, etc.)
        customer_phone: Customer's phone number (MUST use system_caller_id from metadata when available)
        customer_name: Customer's name (optional)
    
    Returns:
        Dictionary with test drive booking confirmation
    """
    import time as time_module
    start_time_log = time_module.time()
    
    try:
        # If customer_phone is not provided, return error
        if not customer_phone:
            return {"error": "Customer phone number is required (use system_caller_id)"}
        
        result = await test_drive_manager.book_test_drive(
            date=date,
            time_slot=time,
            customer_phone=customer_phone,
            customer_name=customer_name
        )
        
        # Log successful call
        duration_ms = (time_module.time() - start_time_log) * 1000
        await tool_logger.log_tool_call(
            tool_name="book_test_drive",
            arguments={
                "date": date,
                "time": time,
                "customer_phone": customer_phone[:6] + "****" if customer_phone else None
            },
            result=result,
            duration_ms=duration_ms
        )
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error booking test drive: {error_msg}")
        
        # Log failed call
        duration_ms = (time_module.time() - start_time_log) * 1000
        result = {"error": error_msg}
        
        await tool_logger.log_tool_call(
            tool_name="book_test_drive",
            arguments={"date": date, "time": time},
            result=result,
            error=error_msg,
            duration_ms=duration_ms
        )
        
        return result


@mcp.tool()
async def join_test_drive_waitlist(
    preferred_date: str,
    preferred_time: str = "any",
    customer_phone: str = None,
    customer_name: str = None
) -> dict:
    """
    Join the waitlist for VW ID.7 test drive when preferred slot is unavailable.
    Maximum 10 people per day on waitlist. Notified via SMS when slot opens.
    
    IMPORTANT: When system_caller_id is available in metadata, use it as customer_phone.
    
    Args:
        preferred_date: Preferred date in YYYY-MM-DD format
        preferred_time: Preferred time slot (09:00, 10:00, etc.) or "any" for any available slot
        customer_phone: Customer's phone number (MUST use system_caller_id from metadata when available)
        customer_name: Customer's name (optional)
    
    Returns:
        Dictionary with waitlist confirmation and position
    """
    start_time = time.time()
    
    try:
        # If customer_phone is not provided, return error
        if not customer_phone:
            return {"error": "Customer phone number is required (use system_caller_id)"}
        
        result = await test_drive_manager.join_waitlist(
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            customer_phone=customer_phone,
            customer_name=customer_name
        )
        
        # Log successful call
        duration_ms = (time.time() - start_time) * 1000
        await tool_logger.log_tool_call(
            tool_name="join_test_drive_waitlist",
            arguments={
                "preferred_date": preferred_date,
                "preferred_time": preferred_time,
                "customer_phone": customer_phone[:6] + "****" if customer_phone else None
            },
            result=result,
            duration_ms=duration_ms
        )
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error joining test drive waitlist: {error_msg}")
        
        # Log failed call
        duration_ms = (time.time() - start_time) * 1000
        result = {"error": error_msg}
        
        await tool_logger.log_tool_call(
            tool_name="join_test_drive_waitlist",
            arguments={"preferred_date": preferred_date, "preferred_time": preferred_time},
            result=result,
            error=error_msg,
            duration_ms=duration_ms
        )
        
        return result




@mcp.tool()
async def get_server_info() -> dict:
    """
    Get information about the VW MCP server
    
    Returns:
        Dictionary with server details
    """
    return {
        "name": "vw-customer-support",
        "version": "0.1.0",
        "transport": "sse",
        "tools": [
            "find_service_centers",
            "lookup_parts", 
            "ask_supervisor",
            "send_whatsapp",
            "send_sms",
            "check_test_drive_availability",
            "book_test_drive",
            "join_test_drive_waitlist",
            "get_server_info"
        ],
        "status": "operational"
    }


# Create the ASGI app for SSE
app = mcp.sse_app()

# Add startup event handler for background tasks
@app.on_event("startup")
async def startup_event():
    """Start background tasks on server startup"""
    # Import here to avoid circular dependencies
    from src.tools.calendar_sync_service import start_calendar_sync
    
    # Get settings
    settings = Settings()
    
    # Start calendar sync service if calendar is configured
    if settings.ID7_CALENDAR_ID and settings.GOOGLE_SERVICE_ACCOUNT_FILE:
        logger.info("Starting calendar sync service...")
        await start_calendar_sync(settings)
        logger.info("Calendar sync service started successfully")
    else:
        logger.warning("Calendar sync service not started - missing configuration")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on server shutdown"""
    from src.tools.calendar_sync_service import get_calendar_sync_service
    
    settings = Settings()
    sync_service = get_calendar_sync_service(settings)
    
    if sync_service.running:
        await sync_service.stop()
        logger.info("Calendar sync service stopped")


if __name__ == "__main__":
    # Run the server with SSE support
    import uvicorn
    
    logger.info("Starting VW Customer Support MCP Server with SSE support")
    logger.info("SSE endpoint will be available at http://0.0.0.0:3000/sse")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3000,
        log_level="info"
    )