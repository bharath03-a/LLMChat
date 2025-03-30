import os
import asyncio
from dotenv import load_dotenv
import argparse
from legal_ai_assistant import LegalAIAssistant
import uvicorn

async def demo_query(query_text):
    """Demo function to test the assistant with a text query"""
    assistant = LegalAIAssistant()
    print(f"Processing query: '{query_text}'")
    result = await assistant.process_query(query_text)
    
    print("\n=== QUERY ANALYSIS ===")
    print(f"Core Legal Issue: {result['query_details'].get('core_legal_issue', 'N/A')}")
    print(f"Jurisdiction: {result['query_details'].get('jurisdiction', 'N/A')}")
    print(f"Legal Domains: {', '.join(result['query_details'].get('legal_domains', ['N/A']))}")
    
    print("\n=== FINAL RESPONSE ===")
    print(result['final_response'])
    
    print("\n=== REFERENCES ===")
    for ref in result.get('references', []):
        print(f"- {ref}")

def start_api():
    """Start the FastAPI server"""
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Legal AI Assistant")
    parser.add_argument("--mode", choices=["api", "demo"], default="api", 
                        help="Run mode: 'api' to start the server, 'demo' for a demonstration")
    parser.add_argument("--query", type=str, help="Query text for demo mode")
    
    args = parser.parse_args()
    
    if args.mode == "api":
        start_api()
    elif args.mode == "demo":
        if not args.query:
            args.query = "What are my rights if my neighbor is making excessive noise at night?"
        asyncio.run(demo_query(args.query))