#!/usr/bin/env python3
"""Test German language support"""

import json
import subprocess

def test_german_chat():
    """Test Claude responding in German"""
    
    # Test data in German
    data = {
        "session_id": "test-de-123",
        "message": "Ich habe 10 Jahre Erfahrung als Projektmanager und möchte mich für diese Stelle bewerben.",
        "job_id": "job_001",
        "job_title": "Senior Projektmanager/in",
        "department": "Betrieb",
        "language": "de",
        "conversation_history": []
    }
    
    # Use curl to test
    cmd = [
        'curl', '-X', 'POST',
        'http://localhost:5010/api/chat',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(data),
        '-s'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            response = json.loads(result.stdout)
            print("✅ German Chat API Test Successful!")
            print("\n📝 Antwort von Claude (auf Deutsch):")
            print(response.get("response", "Keine Antwort"))
            
            if response.get("field_updates"):
                print("\n📋 Feld-Updates erkannt:")
                for field, value in response["field_updates"].items():
                    print(f"  - {field}: {value[:100]}...")
        except json.JSONDecodeError:
            print("❌ Fehler beim Parsen der Antwort")
    else:
        print(f"❌ Fehler: {result.stderr}")

def test_jobs_api():
    """Test that German job data is returned"""
    
    cmd = ['curl', '-s', 'http://localhost:5010/api/jobs']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        jobs = json.loads(result.stdout)
        print("\n📊 Jobs with German translations:")
        for job in jobs:
            if job.get("title_de"):
                print(f"  ✓ {job['title']} → {job['title_de']}")
        
        # Check for the new German-specific jobs
        german_jobs = [j for j in jobs if j['id'] in ['job_005', 'job_006']]
        if german_jobs:
            print(f"\n✅ Found {len(german_jobs)} German-specific jobs")
            for job in german_jobs:
                print(f"  - {job['title_de']} ({job['location_de']})")

if __name__ == "__main__":
    print("Testing German Language Support...")
    print("=" * 50)
    
    print("\n1. Testing Jobs API with German data...")
    test_jobs_api()
    
    print("\n2. Testing Chat API in German...")
    test_german_chat()