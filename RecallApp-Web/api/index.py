"""
Vercel serverless API endpoint for Recall web app.
This handles all backend functionality in a single file for easy deployment.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import parse_qs

# For Vercel, we'll use a simplified in-memory storage for demo
# In production, you'd connect to a database

# Sample data for demonstration
SAMPLE_EVENTS = [
    {
        "id": "1",
        "timestamp": "2025-08-22T14:30:00Z",
        "source": "windrecorder",
        "title": "Working on Recall App Development",
        "text": "Developing the Mac menu bar application with rumps framework",
        "tags": ["coding", "development", "python"],
        "relevance": 0.95
    },
    {
        "id": "2",
        "timestamp": "2025-08-22T13:15:00Z",
        "source": "claude",
        "title": "Claude: Discussion about WindRecorder integration",
        "text": "How to integrate WindRecorder with AI chat logs for unified timeline",
        "tags": ["ai-chat", "claude", "integration"],
        "relevance": 0.88
    },
    {
        "id": "3",
        "timestamp": "2025-08-22T12:00:00Z",
        "source": "windrecorder",
        "title": "Browsing GitHub - yuka-friends/Windrecorder",
        "text": "Researching WindRecorder documentation and API structure",
        "tags": ["research", "browser", "documentation"],
        "relevance": 0.82
    },
    {
        "id": "4", 
        "timestamp": "2025-08-22T10:30:00Z",
        "source": "claude",
        "title": "Claude: Implementing search engine with ChromaDB",
        "text": "Building semantic search functionality using vector embeddings",
        "tags": ["ai-chat", "claude", "search", "development"],
        "relevance": 0.90
    },
    {
        "id": "5",
        "timestamp": "2025-08-21T16:45:00Z",
        "source": "windrecorder",
        "title": "VS Code - editing search_engine.py",
        "text": "Implementing ChromaDB integration for semantic search",
        "tags": ["coding", "vscode", "python"],
        "relevance": 0.75
    }
]

def handler(request, response):
    """
    Main handler for Vercel serverless function.
    Routes requests to appropriate handlers.
    """
    
    # Handle CORS
    response.status_code = 200
    response.headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    }
    
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return response
    
    # Parse the path
    path = request.path.replace('/api', '')
    
    # Route to appropriate handler
    if path == '/search' or path == '/':
        return handle_search(request, response)
    elif path == '/timeline':
        return handle_timeline(request, response)
    elif path == '/stats':
        return handle_stats(request, response)
    elif path == '/events/recent':
        return handle_recent_events(request, response)
    else:
        response.status_code = 404
        response.body = json.dumps({"error": "Not found"})
        return response

def handle_search(request, response):
    """Handle search requests."""
    
    # Get query parameters
    params = parse_qs(request.query_string or '')
    query = params.get('q', [''])[0]
    source_filter = params.get('source', [None])[0]
    limit = int(params.get('limit', [10])[0])
    
    # Filter events based on query
    results = []
    for event in SAMPLE_EVENTS:
        # Simple text matching for demo
        if query.lower() in event['title'].lower() or query.lower() in event['text'].lower():
            if source_filter is None or event['source'] == source_filter:
                results.append(event)
    
    # Sort by relevance and limit
    results.sort(key=lambda x: x['relevance'], reverse=True)
    results = results[:limit]
    
    response.body = json.dumps({
        "query": query,
        "results": results,
        "total": len(results)
    })
    
    return response

def handle_timeline(request, response):
    """Handle timeline requests."""
    
    params = parse_qs(request.query_string or '')
    
    # Parse date range
    start_date = params.get('start', [None])[0]
    end_date = params.get('end', [None])[0]
    
    # For demo, return all events sorted by time
    timeline_events = sorted(SAMPLE_EVENTS, key=lambda x: x['timestamp'], reverse=True)
    
    # Group by hour for timeline view
    grouped_events = {}
    for event in timeline_events:
        # Parse timestamp and group by hour
        dt = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        hour_key = dt.strftime('%Y-%m-%d %H:00')
        
        if hour_key not in grouped_events:
            grouped_events[hour_key] = []
        grouped_events[hour_key].append(event)
    
    response.body = json.dumps({
        "timeline": grouped_events,
        "total_events": len(timeline_events),
        "date_range": {
            "start": start_date or min(e['timestamp'] for e in timeline_events),
            "end": end_date or max(e['timestamp'] for e in timeline_events)
        }
    })
    
    return response

def handle_stats(request, response):
    """Handle statistics requests."""
    
    # Calculate statistics
    total_events = len(SAMPLE_EVENTS)
    
    sources = {}
    for event in SAMPLE_EVENTS:
        source = event['source']
        sources[source] = sources.get(source, 0) + 1
    
    # Recent activity (last 24 hours)
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    recent_count = sum(
        1 for event in SAMPLE_EVENTS 
        if datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')) > yesterday
    )
    
    stats = {
        "total_events": total_events,
        "sources": sources,
        "recent_events_24h": recent_count,
        "last_updated": now.isoformat() + 'Z',
        "database_status": "demo_mode",
        "archive_status": {
            "size_mb": 42.3,
            "age_days": 7,
            "next_archive": "2025-08-29T02:00:00Z"
        }
    }
    
    response.body = json.dumps(stats)
    return response

def handle_recent_events(request, response):
    """Handle recent events requests."""
    
    params = parse_qs(request.query_string or '')
    hours = int(params.get('hours', [4])[0])
    
    # Get events from last N hours
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    recent_events = [
        event for event in SAMPLE_EVENTS
        if datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')) > cutoff_time
    ]
    
    # Sort by timestamp
    recent_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    response.body = json.dumps({
        "events": recent_events,
        "hours": hours,
        "count": len(recent_events)
    })
    
    return response

# For local testing
if __name__ == "__main__":
    # Simple test
    class MockRequest:
        def __init__(self):
            self.path = "/api/search"
            self.method = "GET"
            self.query_string = "q=claude"
    
    class MockResponse:
        def __init__(self):
            self.status_code = None
            self.headers = {}
            self.body = None
    
    req = MockRequest()
    res = MockResponse()
    handler(req, res)
    print(res.body)