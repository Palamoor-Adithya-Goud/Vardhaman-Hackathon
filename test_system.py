"""
Automated system verification script.
Tests intent classification, RAG retrieval, collaboration matchmaking, and professor gap analysis mode.
"""

from db.init_db import init_database
from agents.chat_agent import ChatAgent
from memory.memory_store import MemoryStore

def test_query(agent, query_text):
    print("\n" + "=" * 60)
    print(f"Testing Query: '{query_text}'")
    print("=" * 60)
    
    result = agent.run_query(query_text)
    print(f"Detected Intent: {result['intent']}")
    print(f"\nResponse:\n{result['response_text']}")

def main():
    print("Initializing Database tables...")
    init_database()
    
    agent = ChatAgent()
    
    # 1. Test general expert RAG search
    test_query(agent, "Who works on Federated Learning?")
    
    # 2. Test collaboration matching
    test_query(agent, "Suggest collaboration between Padmaja and Madhurya")
    
    # 3. Test Professor Mode (Gap analysis)
    test_query(agent, "Professor mode: IoT and Edge Computing")
    
    # 4. Test Edge Case - Capabilities / greetings query
    test_query(agent, "what are the capabilites of you")
    
    # 5. Test Edge Case - Off-topic query
    test_query(agent, "Can you tell me how to make a pepperoni pizza?")
    
    # 6. Test Multi-Author extraction check
    test_query(agent, "Who works on recommendation trust?")

if __name__ == "__main__":
    main()
