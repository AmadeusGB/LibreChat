#!/usr/bin/env python3
"""
Simple command-line interface for Rust Agent Workflow API
Supports streaming responses with real-time progress display.
"""

import json
import sys
import requests
from typing import Dict, Any, Union, Optional

API_URL = "https://agent-workflow-993464051590.us-central1.run.app/v1/responses"

def create_request_payload(user_input: str) -> Dict[str, Any]:
    """Create the API request payload."""
    return {
        "input": user_input,
        "temperature": 0,
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 8192,
        "use_rag": True,
        "stream": True
    }

def parse_sse_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a Server-Sent Events data line."""
    line = line.strip()
    if line.startswith("data: "):
        try:
            json_data = line[6:]  # Remove "data: " prefix
            return json.loads(json_data)
        except json.JSONDecodeError:
            return None
    return None

def format_progress(progress: float, message: str, event: str) -> str:
    """Format progress display."""
    bar_length = 30
    filled_length = int(bar_length * progress / 100)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    return f"\r[{bar}] {progress:5.1f}% | {event} | {message}"

def extract_clean_response(data: Dict[str, Any]) -> str:
    """Extract clean response content from the API response."""
    # Try to get the actual text content from choices
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]
    
    # Fallback to other content fields
    if "content" in data:
        return data["content"]
    elif "message" in data:
        return data["message"]
    
    return json.dumps(data, indent=2)

def should_show_progress(event: str) -> bool:
    """Determine if this event should be shown in progress."""
    # Show key workflow events, hide verbose metadata events
    important_events = {
        "workflow.started", 
        "workflow.prompt", 
        "workflow.response", 
        "workflow.code_extraction",
        "workflow.cargo_check",
        "workflow.evaluation"
    }
    return event in important_events

def stream_response(user_input: str):
    """Stream the API response with real-time updates."""
    payload = create_request_payload(user_input)
    
    print(f"\n🤖 Asking: {user_input}")
    print("=" * 60)
    
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=300
        )
        response.raise_for_status()
        
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
                
            data = parse_sse_line(line)
            if not data:
                continue
            
            is_final = data.get("is_final", False)
            
            if not is_final:
                # Show intermediate progress for important events only
                event = data.get("event", "unknown")
                if should_show_progress(event):
                    progress = data.get("progress", 0.0)
                    message = data.get("message", "Processing...")
                    
                    progress_line = format_progress(progress, message, event)
                    print(progress_line, end="", flush=True)
            else:
                # Final response - clear progress and show clean result
                print("\n" + "=" * 60)
                
                # Extract clean content
                clean_content = extract_clean_response(data)
                
                print("\n📝 Answer:")
                print("-" * 40)
                print(clean_content)
                
                # Show compilation status if available
                if isinstance(data, dict) and "cargo_check" in data:
                    cargo_result = data["cargo_check"]
                    if cargo_result.get("success"):
                        print(f"\n✅ Code compilation: SUCCESS")
                    else:
                        print(f"\n❌ Code compilation: FAILED")
                        if "diagnostics" in cargo_result:
                            print("Errors:")
                            for diag in cargo_result["diagnostics"][:3]:  # Show first 3 errors
                                print(f"  • {diag.get('message', 'Unknown error')}")
                
                break
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: {e}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return False
    
    return True

def main():
    """Main interactive loop."""
    print("🦀 Rust Agent CLI")
    print("Type your questions or 'quit' to exit")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question.")
                continue
            
            success = stream_response(user_input)
            if not success:
                print("\nFailed to get response. Try again or type 'quit' to exit.")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()