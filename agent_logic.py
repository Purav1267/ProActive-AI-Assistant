# agent_logic.py
# This file contains the core logic for the ProActive AI Assistant.
# It manages conversation history, integrates with various tools (Google Calendar, Restaurant Search),
# handles natural language understanding, and executes tasks based on user commands.

import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import json
import re
import dateparser # Ensure dateparser is installed (pip install dateparser)

# --- Initial Setup ---

# Load environment variables from a .env file for secure configuration.
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Ensure the Google API key is set, as it's required for the generative AI model.
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables. Please set it.")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Tool Integration ---

# Import custom tool modules.
import tools.google_calendar as google_calendar
import tools.restaurant_search as restaurant_search
import tools.Google_Search as google_search_tool # Corrected alias
from prompts import SYSTEM_INSTRUCTION, TEAM_MEMBERS_INITIAL

# Map tool names (as the LLM will call them) to their corresponding Python functions.
# This provides a clean interface for the model to request tool execution.
available_tools = {
    "check_calendar_availability": google_calendar.check_calendar_availability,
    "send_calendar_invite": google_calendar.send_calendar_invite,
    "search_restaurants": restaurant_search.search_restaurants,
    "google_search": google_search_tool.search, # Corrected usage of the alias
}

# --- State Management ---
# These global variables maintain the state of the conversation and cached results.

# Stores the entire conversation history to provide context to the LLM.
# It should be a list of dictionaries, each representing a turn.
conversation_history = [] 
# Caches available calendar slots to avoid redundant API calls.
available_slots_cache = []
# Caches restaurant search results.
found_restaurants_cache = []
# Maintains a dynamic list of team members' emails.
current_team_members = list(TEAM_MEMBERS_INITIAL)

# --- Helper Functions ---

def extract_emails(text: str) -> list:
    """
    Extracts unique email addresses from a given text using a simple regex.
    This is used by main.py to quickly identify and add new team members.

    Args:
        text: The input string to search for emails.

    Returns:
        A list of unique email addresses found in the text.
    """
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return list(set(emails))

def update_team_members(new_emails: list):
    """
    Adds new email addresses to the global list of team members.

    Args:
        new_emails: A list of email addresses to add.
    """
    global current_team_members
    for email in new_emails:
        if email not in current_team_members:
            current_team_members.append(email)
            # Removed print statement: (Internal) Added '{email}' to known team members list.

def convert_datetimes_to_iso(obj):
    """
    Recursively converts datetime objects within a data structure to ISO 8601 string format.
    The Gemini API requires JSON-serializable data, and this ensures compatibility.

    Args:
        obj: The object (dict, list, datetime) to process.

    Returns:
        The processed object with datetimes converted to strings.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, list):
        return [convert_datetimes_to_iso(elem) for elem in obj]
    elif isinstance(obj, dict):
        return {k: convert_datetimes_to_iso(v) for k, v in obj.items()}
    else:
        return obj

def resolve_datetime_from_string(date_time_str: str, current_context_date: datetime, timezone_name: str) -> datetime:
    """
    Parses a natural language date/time string into a timezone-aware datetime object.
    It uses the `dateparser` library for flexibility and has a regex-based fallback
    for common patterns like "next Tuesday at 5pm".

    Args:
        date_time_str: The natural language string to parse (e.g., "tomorrow", "next Friday at 3pm").
        current_context_date: The current datetime, used as a reference for relative dates.
        timezone_name: The target timezone (e.g., "Asia/Kolkata").

    Returns:
        A timezone-aware datetime object.

    Raises:
        ValueError: If the date/time string cannot be parsed.
    """
    tz = pytz.timezone(timezone_name)

    # 1. Use dateparser for robust, flexible parsing.
    settings = {
        'RETURN_AS_TIMEZONE_AWARE': True,
        'RELATIVE_BASE': current_context_date,
        'TO_TIMEZONE': timezone_name,
        'DATE_ORDER': 'YMD', # Or MDY depending on your preferred default
        'PREFER_DATES_FROM': 'future' # Prefer dates in the future
    }
    
    parsed_dt = dateparser.parse(date_time_str, settings=settings)

    if parsed_dt:
        # Ensure the final datetime is in the correct timezone.
        return parsed_dt.astimezone(tz)

    # 2. Fallback for common patterns if dateparser returns None.
    date_time_str_lower = date_time_str.lower().strip()
    match = re.search(r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+at\s+(\d{1,2})\s*(pm|am)?', date_time_str_lower)
    
    if match:
        day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
        target_day_name = match.group(1)
        hour_str = match.group(2)
        ampm = match.group(3)

        target_day_of_week = day_map[target_day_name]
        today_weekday = current_context_date.weekday()
        
        days_ahead = (target_day_of_week - today_weekday + 7) % 7
        if days_ahead == 0:
            days_ahead = 7  # If today is Tuesday and we ask for "next Tuesday", it means 7 days from now.

        target_date = current_context_date.date() + timedelta(days=days_ahead)
        
        hour = int(hour_str)
        if ampm == 'pm' and hour != 12:
            hour += 12
        elif ampm == 'am' and hour == 12: # Handle 12 AM as midnight
            hour = 0
        
        resolved_dt = tz.localize(datetime(target_date.year, target_date.month, target_date.day, hour, 0, 0))
        return resolved_dt

    # 3. If all methods fail, raise a clear error.
    raise ValueError(f"Could not parse datetime: '{date_time_str}'. Please provide a clearer date/time (e.g., 'YYYY-MM-DD HH:MM').")

def get_updated_system_instruction() -> str:
    """
    Dynamically generates the system instruction for the LLM.
    This includes the current date/time, timezone, and the list of team members,
    providing the model with up-to-date context for every turn.

    Returns:
        A formatted string containing the full system instruction.
    """
    current_datetime_aware = datetime.now(pytz.timezone(google_calendar.CALENDAR_TIMEZONE))
    formatted_datetime = current_datetime_aware.strftime("%Y-%m-%d %H:%M:%S %Z%z")
    team_members_str = "\n".join([f"- {member}" for member in current_team_members])

    return SYSTEM_INSTRUCTION.format(
        current_datetime=formatted_datetime,
        current_timezone=google_calendar.CALENDAR_TIMEZONE,
        team_members=team_members_str
    )

# --- Main Agent Handler ---

def handle_user_input(user_input: str) -> str: # Added return type hint
    """
    The main entry point for processing user input.
    This function orchestrates the entire agent workflow:
    1. Updates the system instruction with the latest context.
    2. Sends the user query to the Gemini model.
    3. Handles the model's response, which may include text or tool calls.
    4. Executes tools, caches results, and sends results back to the model.
    5. Returns the final text response to the user.
    """
    global conversation_history, available_slots_cache, found_restaurants_cache

    # Always get the fresh system instruction with current context.
    updated_system_instruction = get_updated_system_instruction()

    # Initialize the Gemini model for this turn.
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        tools=[
            google_calendar.check_calendar_availability,
            google_calendar.send_calendar_invite,
            restaurant_search.search_restaurants,
            google_search_tool.search
        ],
        system_instruction=updated_system_instruction
    )

    # The first message to the chat session should be the user's input for the current turn.
    # The `history` parameter in `start_chat` handles the preceding conversation.
    # We DO NOT append user_input to conversation_history here before `start_chat`
    # if `send_message` is going to send `user_input` directly.
    # Instead, `start_chat` gets the full history *up to the previous turn*,
    # and `send_message` sends the *current* user input.

    # Start a chat session with the conversation history up to the previous turn.
    chat = model.start_chat(history=conversation_history)
    
    # Send the current user input as the new message in the chat.
    response = chat.send_message(user_input)

    # After the model responds to the user's input, add the user's turn to history
    # This is crucial for the next turn's context.
    conversation_history.append({"role": "user", "parts": [user_input]})
    
    # And add the model's response to history
    if response.candidates and response.candidates[0].content.parts:
        conversation_history.append(response.candidates[0].content)


    final_assistant_response_text = "" # Initialize variable to store the final text response

    # Loop to handle potential multi-step tool interactions.
    while True:
        if response.candidates and response.candidates[0].content.parts:
            tool_call_parts = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
            text_response_parts = [part.text for part in response.candidates[0].content.parts if part.text]

            if tool_call_parts:
                tool_responses_for_history = [] # Collect all tool responses for this turn
                for function_call in tool_call_parts:
                    function_name = function_call.name
                    function_args = dict(function_call.args)

                    if function_name in available_tools:
                        try:
                            # Pre-process arguments, especially for resolving datetime strings.
                            if function_name in ["check_calendar_availability", "send_calendar_invite"]:
                                current_dt_for_context = datetime.now(pytz.timezone(google_calendar.CALENDAR_TIMEZONE))
                                
                                dt_string_keys = {
                                    'search_start_dt_str': 'search_start_dt',
                                    'search_end_dt_str': 'search_end_dt',
                                    'slot_datetime_start_str': 'slot_datetime_start',
                                    'slot_datetime_end_str': 'slot_datetime_end',
                                }

                                for key_str, key_dt in dt_string_keys.items():
                                    datetime_string = None
                                    if key_str in function_args:
                                        datetime_string = function_args.pop(key_str)
                                    elif key_dt in function_args and isinstance(function_args[key_dt], str):
                                        datetime_string = function_args.pop(key_dt)
                                    
                                    if datetime_string:
                                        function_args[key_dt] = resolve_datetime_from_string(
                                            datetime_string,
                                            current_dt_for_context,
                                            google_calendar.CALENDAR_TIMEZONE
                                        )

                                if 'slot_duration_minutes' in function_args and isinstance(function_args['slot_duration_minutes'], float):
                                    function_args['slot_duration_minutes'] = int(function_args['slot_duration_minutes'])

                            tool_result = available_tools[function_name](**function_args)

                            if function_name == "check_calendar_availability":
                                available_slots_cache[:] = tool_result # Use slice assignment to update global list in place
                            elif function_name == "search_restaurants":
                                found_restaurants_cache[:] = tool_result # Use slice assignment to update global list in place

                            # Prepare the tool's result to be sent back to the model.
                            # Ensure the response is always a dictionary, even if the tool_result is a list.
                            processed_tool_result = convert_datetimes_to_iso(tool_result)
                            # Wrap the processed_tool_result in a dictionary
                            response_payload = {"output": processed_tool_result}
                            tool_responses_for_history.append({"function_response": {"name": function_name, "response": response_payload}})

                        except Exception as e:
                            error_msg = f"Error executing tool {function_name}: {e}"
                            response_payload = {"error_message": error_msg} # Wrap error in a dict
                            tool_responses_for_history.append({"function_response": {"name": function_name, "response": response_payload}})
                    else:
                        error_msg = f"Tool '{function_name}' not found."
                        response_payload = {"error_message": error_msg} # Wrap error in a dict
                        tool_responses_for_history.append({"function_response": {"name": function_name, "response": response_payload}})

                # Add all tool responses for this turn to conversation history.
                history_entry = {"role": "tool", "parts": tool_responses_for_history}
                conversation_history.append(history_entry)

                # Send the tool results back to the model to get the next response.
                response = chat.send_message(history_entry['parts'])

            elif text_response_parts:
                final_assistant_response_text = " ".join(text_response_parts)
                conversation_history.append({"role": "model", "parts": [final_assistant_response_text]})
                return final_assistant_response_text # Return the text response

            else:
                final_assistant_response_text = "I processed the request but have no specific response. Is there anything else I can help with?"
                conversation_history.append({"role": "model", "parts": [final_assistant_response_text]})
                return final_assistant_response_text

        else:
            final_assistant_response_text = "I'm not sure how to respond to that. Can you please rephrase or provide more details?"
            conversation_history.append({"role": "model", "parts": [final_assistant_response_text]})
            return final_assistant_response_text