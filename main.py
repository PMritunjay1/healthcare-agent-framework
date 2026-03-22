# main.py

from orchestrator import Orchestrator

if __name__ == "__main__":
    orchestrator = Orchestrator()
    
    print("\n" + "="*50)
    print("      Welcome to the FREE Healthcare Automation Framework")
    print("="*50)
    print("This system runs 100% locally on your computer using Ollama.")
    print("\nExample Commands:")
    print("  - I need a summary for Sarah Tancredi")
    print("  - enter a new note for Robert Paulson: Patient is improving.")
    print("  - schedule an appointment for Emily Carter on 2025-10-15")
    print("\nType 'exit' to quit.")
    print("\nType 'exit' to quit.")


    while True:
        user_query = input("\n> ")
        if user_query.lower() == 'exit':
            print("Exiting. Goodbye!")
            break
        result = orchestrator.run(user_query)
        print(f"\n[Final Answer]: {result}")