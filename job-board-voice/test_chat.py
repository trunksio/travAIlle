#!/usr/bin/env python3
"""Test script for the Claude chat API"""

import requests
import json

# Test the chat endpoint
def test_chat():
    url = "http://localhost:5010/api/chat"
    
    # Test message that should trigger field population
    test_data = {
        "session_id": "test-session-123",
        "message": "I have 10 years of experience in project management and have led cross-functional teams. I'm interested in this role because it aligns with my leadership skills.",
        "job_id": "job_001",
        "job_title": "Senior Project Manager",
        "department": "Operations",
        "conversation_history": []
    }
    
    try:
        response = requests.post(url, json=test_data)
        if response.status_code == 200:
            data = response.json()
            print("✅ Chat API Test Successful!")
            print("\n📝 Response from Claude:")
            print(data.get("response", "No response"))
            print("\n📋 Field Updates Detected:")
            field_updates = data.get("field_updates", {})
            if field_updates:
                for field, value in field_updates.items():
                    print(f"  - {field}: {value[:100]}..." if len(value) > 100 else f"  - {field}: {value}")
            else:
                print("  No fields to update yet")
        else:
            print(f"❌ Error: Status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure the backend is running and your API key is configured")

if __name__ == "__main__":
    print("Testing Claude Chat Integration...")
    print("-" * 50)
    test_chat()