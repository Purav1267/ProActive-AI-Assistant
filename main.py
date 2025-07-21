import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env file. Please set it.")
    exit()

# Configure Generative AI (ensure this is done before importing agent_logic as it uses genai)
genai.configure(api_key=GOOGLE_API_KEY)

# Import the main logic from agent_logic.py
from agent_logic import handle_user_input, extract_emails, update_team_members, available_slots_cache, found_restaurants_cache
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
        # A simple heuristic to allow the user to add team members quickly.
        # This will update agent_logic.current_team_members directly.
        found_emails = extract_emails(user_query)
        if found_emails:
            update_team_members(found_emails)

        # Call the agent's main handler
        handle_user_input(user_query)

        # After handle_user_input, the agent_logic might have populated caches.
        # The LLM itself in agent_logic is designed to then use these caches
        # and prompt the user for the next action (e.g., "Would you like me to book?").
        # So, no further explicit logic is needed here in main() for booking.

if __name__ == "__main__":
    main()