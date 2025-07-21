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
import dateparser

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
import tools.Google_Search as google_search_tool
from prompts import SYSTEM_INSTRUCTION, TEAM_MEMBERS_INITIAL

# Map tool names (as the LLM will call them) to their corresponding Python functions.
# This provides a clean interface for the model to request tool execution.
available_tools = {
    "check_calendar_availability": google_calendar.check_calendar_availability,
    "send_calendar_invite": google_calendar.send_calendar_invite,
    "search_restaurants": restaurant_search.search_restaurants,
    "Google Search": google_search_tool.search,
}

# --- State Management ---
# These global variables maintain the state of the conversation and cached results.

# Stores the entire conversation history to provide context to the LLM.
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
            print(f"(Internal) Added '{email}' to known team members list.")

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
        timezone_name: The target timezone (e.g., "America/New_York").

    Returns:
        A timezone-aware datetime object.

    Raises:
        ValueError: If the date/time string cannot be parsed.
    """
    tz = pytz.timezone(timezone_name)

    # 1. Use dateparser for robust, flexible parsing.
    try:
        settings = {
            'RETURN_AS_TIMEZONE_AWARE': True,
            'RELATIVE_BASE': current_context_date,
            'TO_TIMEZONE': timezone_name
        }
        parsed_dt = dateparser.parse(date_time_str, settings=settings)
        if parsed_dt:
            # Ensure the final datetime is in the correct timezone.
            return parsed_dt.astimezone(tz)
    except Exception as e:
        print(f"(Internal) dateparser failed with error: {e}. Trying regex fallback.")

    # 2. Fallback for "next [weekday] at [time]" patterns.
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
        print(f"(Internal FALLBACK) Parsed '{date_time_str}' to {resolved_dt}")
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

def handle_user_input(user_input: str):
    """
    The main entry point for processing user input.
    This function orchestrates the entire agent workflow:
    1. Updates the system instruction with the latest context.
    2. Sends the user query to the Gemini model.
    3. Handles the model's response, which may include text or tool calls.
    4. Executes tools, caches results, and sends results back to the model.
    5. Prints the final text response to the user.
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

    # Append the user's message to the conversation history.
    conversation_history.append({"role": "user", "parts": [user_input]})

    # Start a chat session and send the message.
    chat = model.start_chat(history=conversation_history)
    response = chat.send_message(user_input)

    # IMPORTANT: The model's response (including any tool calls) must be added
    # back to our history to maintain a coherent conversation record.
    if response.candidates and response.candidates[0].content.parts:
        conversation_history.append(response.candidates[0].content)

    # Verbose debug printing to inspect the raw model output.
    print("\n--- RAW GEMINI RESPONSE CONTENT (VERBOSE) ---")
    if response.candidates:
        if response.candidates[0].content.parts:
            for i, part in enumerate(response.candidates[0].content.parts):
                print(f"Part {i+1} Type: {type(part)}")
                if part.function_call:
                    print(f"  FUNCTION CALL ATTEMPTED: {part.function_call.name}({part.function_call.args})")
                elif part.text:
                    print(f"  TEXT RESPONSE: {part.text}")
                else:
                    print(f"  UNEXPECTED PART CONTENT (type {type(part.value)}): {part}")
        else:
            print("  Response candidate content.parts is empty.")
    else:
        print("  No candidates in response.")
    print(f"Full Raw Response Object (for deeper inspection): {response}") # Print the entire response object
    print("--- END RAW GEMINI RESPONSE CONTENT (VERBOSE) ---")

    # Loop to handle potential multi-step tool interactions.
    while True:
        if response.candidates and response.candidates[0].content.parts:
            tool_call_parts = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
            text_response_parts = [part.text for part in response.candidates[0].content.parts if part.text]

            if tool_call_parts:
                # The model has requested to use a tool.
                tool_responses = []
                for function_call in tool_call_parts:
                    function_name = function_call.name
                    function_args = dict(function_call.args)

                    print(f"\n--- Model requesting Tool Call: {function_name} with args: {function_args} ---")

                    if function_name in available_tools:
                        try:
                            # Pre-process arguments, especially for resolving datetime strings.
                            if function_name in ["check_calendar_availability", "send_calendar_invite"]:
                                current_dt_for_context = datetime.now(pytz.timezone(google_calendar.CALENDAR_TIMEZONE))
                                
                                # Keys that might contain datetime strings. This makes the logic robust
                                # against the LLM using either 'search_start_dt' or 'search_start_dt_str'.
                                dt_string_keys = {
                                    'search_start_dt_str': 'search_start_dt',
                                    'search_end_dt_str': 'search_end_dt',
                                    'slot_datetime_start_str': 'slot_datetime_start',
                                    'slot_datetime_end_str': 'slot_datetime_end',
                                }

                                for key_str, key_dt in dt_string_keys.items():
                                    # Handle cases where LLM uses either key_str or key_dt with a string value
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

                                # Ensure slot_duration_minutes is an int (from float if LLM outputs float)
                                if 'slot_duration_minutes' in function_args and isinstance(function_args['slot_duration_minutes'], float):
                                    function_args['slot_duration_minutes'] = int(function_args['slot_duration_minutes'])

                            # Execute the requested tool function.
                            tool_result = available_tools[function_name](**function_args)
                            print(f"--- Tool Call Successful. Result: {tool_result} ---")

                            # Cache results for future reference in the conversation.
                            if function_name == "check_calendar_availability":
                                available_slots_cache = tool_result
                            elif function_name == "search_restaurants":
                                found_restaurants_cache = tool_result

                            # Prepare the tool's result to be sent back to the model.
                            processed_tool_result = convert_datetimes_to_iso(tool_result)
                            response_payload = {"result": processed_tool_result}
                            tool_responses.append({"function_response": {"name": function_name, "response": response_payload}})

                        except Exception as e:
                            # Handle errors during tool execution gracefully.
                            error_msg = f"Error executing tool {function_name}: {e}"
                            print(error_msg)
                            tool_responses.append({"function_response": {"name": function_name, "response": {"error": error_msg}}})
                    else:
                        # Handle cases where the model hallucinates a non-existent tool.
                        error_msg = f"Tool '{function_name}' not found."
                        print(error_msg)
                        tool_responses.append({"function_response": {"name": function_name, "response": {"error": error_msg}}})

                # Add the tool responses to our history log.
                history_entry = {"role": "tool", "parts": tool_responses}
                conversation_history.append(history_entry)

                # Send the tool results back to the model to get the next response.
                response = chat.send_message(history_entry['parts'])

            elif text_response_parts:
                # The model has generated a simple text response.
                full_text_response = " ".join(text_response_parts)
                print(f"\nAssistant: {full_text_response}")
                conversation_history.append({"role": "model", "parts": [full_text_response]})
                break  # Exit the loop as we have a final answer for this turn.

            else:
                # Fallback for unexpected response structures.
                print("\nAssistant: I processed the request but have no specific response.")
                break

        else:
            # Fallback if the model provides no response candidates.
            print("\nAssistant: I'm not sure how to respond to that.")
            break