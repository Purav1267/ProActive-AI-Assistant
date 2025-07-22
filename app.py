import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json 
import io
from contextlib import redirect_stdout

# Import your core agent logic and tools
from agent_logic import handle_user_input, extract_emails, update_team_members, available_slots_cache, found_restaurants_cache
import agent_logic 
import tools.google_calendar as google_calendar 

# --- Configuration & Initialization ---

# Load environment variables from .env file
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Stop Streamlit app if API key is missing
if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY not found in .env file. Please set it in your project's root directory.")
    st.stop() 

# Configure Generative AI
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Google Calendar Service once per session
if "calendar_service_initialized" not in st.session_state:
    st.session_state.calendar_service_initialized = False

if not st.session_state.calendar_service_initialized:
    st.info("Initializing Google Calendar service. A browser window may open for authentication on first run.")
    google_calendar.calendar_service = google_calendar.get_calendar_service()
    if google_calendar.calendar_service:
        st.session_state.calendar_service_initialized = True
        st.success("Google Calendar service initialized successfully!")
    else:
        st.error("Failed to initialize Google Calendar service. Please check your cred.json and network connection. Restart the app after fixing.")
        st.stop()

# --- Streamlit UI Setup ---

st.set_page_config(page_title="Proactive AI Assistant", page_icon="🤖", layout="centered")

st.title("🤖 Proactive AI Assistant")
st.markdown("Your smart helper for organizing team dinners!")

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "AI Assistant is ready! How can I help you organize a team dinner?"})
    st.session_state.messages.append({"role": "assistant", "content": f"Initial team members: {', '.join(agent_logic.current_team_members)}"})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What's your request?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            f = io.StringIO()
            with redirect_stdout(f):
                found_emails = extract_emails(prompt)
                if found_emails:
                    update_team_members(found_emails)
                
                # Call agent logic, which now RETURNS the assistant's text response
                assistant_text_response = handle_user_input(prompt) 

            internal_log = f.getvalue() # Get the full internal log (for expander)

            # Display the assistant's conversational response
            st.markdown(assistant_text_response)
            st.session_state.messages.append({"role": "assistant", "content": assistant_text_response})
            
            # --- REMOVED DIRECT DISPLAY OF CACHED RESTAURANTS AND SLOTS ---
            # These will now only be displayed if the LLM explicitly formats them in its text response.
            
            # Optional: Display full internal log in an expander for debugging
            with st.expander("Show Internal Agent Log"):
                st.code(internal_log)
                st.session_state.messages.append({"role": "assistant", "content": "Internal Log:\n```\n" + internal_log + "\n```"})


# --- Sidebar for additional controls/info ---
with st.sidebar:
    st.header("Project Info")
    st.write("This is a proactive AI assistant for organizing team dinners.")
    st.write("Developed using Google Gemini, Google Places API, and Google Calendar API.")
    
    st.markdown("---")
    st.subheader("Controls")
    if st.button("Clear Chat History", help="Clears all messages from the chat."):
        st.session_state.clear()
        st.rerun() 

    st.markdown("---")
    st.subheader("Current Team Members")
    st.write(", ".join(agent_logic.current_team_members))
    st.info("You can add more team members by mentioning their email IDs in your query.")