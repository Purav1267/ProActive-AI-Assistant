import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env file. Please set it.")
    exit()

# Configure Generative AI (ensure this is done before importing agent_logic)
genai.configure(api_key=GOOGLE_API_KEY)

# Import the main logic from agent_logic.py
from agent_logic import handle_user_input, extract_emails, update_team_members
import agent_logic # Import the module to access its current_team_members list


def main():
    print("AI Assistant is ready! Type 'exit' to quit.")
    print("Initial team members: " + ", ".join(agent_logic.current_team_members)) # Display initial team members

    while True:
        user_query = input("\nYou: ")
        if user_query.lower() == 'exit':
            print("Assistant: Goodbye!")
            break
        
        # --- Pre-processing for explicit email updates ---
        found_emails = extract_emails(user_query)
        if found_emails:
            update_team_members(found_emails)

        # Call the agent's main handler, which now RETURNS the assistant's response
        assistant_response = handle_user_input(user_query)
        
        # --- NEW: Print the assistant's response to the console ---
        print(f"\nAssistant: {assistant_response}") 
        # --- END NEW ---

if __name__ == "__main__":
    main()