"""
Faculty Research RAG & Collaboration Intelligence Platform CLI.
Direct chat interface featuring conversational RAG, collaboration matchmaking,
trend/gap analysis, confirmation logging, and interactive feedback.
"""

import sys
from db.init_db import init_database
from agents.chat_agent import ChatAgent
from memory.memory_store import MemoryStore
from core.logger import logger

def main():
    print("=" * 65)
    print("  Faculty Research Assistant RAG + Collaboration Platform")
    print("=" * 65)
    
    # 1. Initialize DB tables
    try:
        init_database()
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)
        
    # 2. Instantiate main orchestrator and memory store
    chat_agent = ChatAgent()
    memory = MemoryStore()
    
    print("\nAsk questions like: 'Who works on Federated Learning?' or 'Professor mode: IoT'")
    print("Type 'exit' or 'quit' to terminate the session.\n")
    
    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
            
        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print("Goodbye!")
            break
            
        # Run query through intent router
        try:
            result = chat_agent.run_query(query)
            intent = result["intent"]
            response_text = result["response_text"]
            data = result["data"]
            
            print(f"\nAssistant:\n{response_text}\n")
            
            # CRITICAL Confirmation prompt
            confirm = input("Shall I proceed and log this recommendation? (yes/no): ").strip().lower()
            if confirm in ("yes", "y"):
                # Save to database
                query_log_id = memory.log_query(
                    query_text=query,
                    response_text=response_text,
                    mode=intent
                )
                
                if query_log_id != -1:
                    # Save context-specific data
                    if intent == "rag":
                        recs = []
                        for m in data.get("internal_matches", []):
                            recs.append({
                                "faculty_name": m["metadata"].get("source", "Unknown"),
                                "reasoning": m["document"][:200] + "...",
                                "is_fallback": data.get("is_fallback_active", False)
                            })
                        memory.log_recommendations(query_log_id, recs)
                        
                    elif intent == "collaborate":
                        memory.log_collaborations(query_log_id, [{
                            "faculty_a": data.get("faculty_a", "Unknown"),
                            "faculty_b": data.get("faculty_b", "Unknown"),
                            "synergy_reason": data.get("synergy_reason", ""),
                            "project_idea": data.get("project_idea", "")
                        }])
                        
                    elif intent == "project":
                        memory.log_projects(query_log_id, [{
                            "title": "Topic-based Project Proposal",
                            "description": data.get("project_suggestion", ""),
                            "target_faculty": data.get("topic", "")
                        }])
                        
                    print("Recommendation successfully logged.")
                    
                    # FeedBack system
                    feedback_input = input("Would you like to rate this response? (1-5, or press Enter to skip): ").strip()
                    if feedback_input.isdigit():
                        rating = int(feedback_input)
                        comments = input("Any comments? (Optional): ").strip()
                        memory.log_user_feedback(
                            query_log_id=query_log_id,
                            rating=rating,
                            comments=comments if comments else None
                        )
                        print("Thank you for your feedback!")
                    else:
                        print("Feedback skipped.")
                else:
                    print("Error: Could not record log entry.")
            else:
                print("Logging cancelled.")
                
            print("-" * 65 + "\n")
            
        except Exception as e:
            print(f"\nAn error occurred processing your query: {e}\n")

if __name__ == "__main__":
    main()
