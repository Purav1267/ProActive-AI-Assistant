# main.py
# This script serves as the main entry point for the ProActive AI Assistant.
# It handles user interaction, environment variable loading, and orchestrates the agent's logic.

import google.generativeai as genai
import os
from dotenv import load_dotenv
from agent_logic import handle_user_input, extract_emails, update_team_members
import agent_logic 

def main():
    """
    The main function that runs the assistant's interactive loop.
    """
    print("AI Assistant is ready! Type 'exit' to quit.")
    
    # --- Initial Setup ---
    # Load environment variables from a .env file for secure key management.
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Ensure the Google API key is available before proceeding.
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY not found in .env file. Please set it.")
        exit()

    # Configure the generative AI model with the API key.
    # This must be done before importing any modules that use `genai`.
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Display the initial list of team members from the agent's state.
    print("Initial team members: " + ", ".join(agent_logic.current_team_members))

    # --- Main Interaction Loop ---
    # The assistant will continuously listen for user input until 'exit' is typed.
    while True:
        user_query = input("\nYou: ")
        if user_query.lower() == 'exit':
            print("Assistant: Goodbye!")
            break
        
        # --- Pre-processing for Team Member Updates ---
        # A simple mechanism to quickly add or update team members via their email addresses.
        # This allows for on-the-fly modifications to the agent's context.
        found_emails = extract_emails(user_query)
        if found_emails:
            update_team_members(found_emails)

        # --- Core Agent Logic ---
        # The user's query is passed to the main handler in `agent_logic.py`
        # where the heavy lifting of understanding and responding happens.
        handle_user_input(user_query)

        # Note: The agent's design is such that after finding information (like available slots
        # or restaurants), it stores this in caches within `agent_logic`. The LLM is then
        # prompted to ask the user for the next step (e.g., "Would you like me to book?").
        # This keeps the main loop simple and delegates complex conversational
        # flows to the agent itself.

if __name__ == "__main__":
    # This ensures that the main() function is called only when the script is executed directly.
    main()