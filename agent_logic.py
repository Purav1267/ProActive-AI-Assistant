import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import json
import re
import dateparser # Restoring for robust date parsing

# Load environment variables (ensure this is done before using os.getenv)
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Generative AI with your API key
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file or environment variables. Please set it.")
genai.configure(api_key=GOOGLE_API_KEY)

# Import your tools
import tools.google_calendar as google_calendar
import tools.restaurant_search as restaurant_search
import tools.Google_Search as google_search_tool
from prompts import SYSTEM_INSTRUCTION, TEAM_MEMBERS_INITIAL # Import system instruction and initial team members

# Map of tool names (as expected by LLM - now unqualified names) to their actual function objects
available_tools = {
    "check_calendar_availability": google_calendar.check_calendar_availability,
    "send_calendar_invite": google_calendar.send_calendar_invite,
    "search_restaurants": restaurant_search.search_restaurants,
    "Google Search": google_search_tool.search,
}

# --- Conversation State Management ---
conversation_history = []
# Cache to store available slots after a check_calendar_availability call
available_slots_cache = []
# Cache to store found restaurants after a search_restaurants call
found_restaurants_cache = []
# Store known team members, can be dynamically updated or extended
current_team_members = list(TEAM_MEMBERS_INITIAL)

# --- Helper Functions ---

# Helper function to extract emails from text (used by main.py)
def extract_emails(text: str) -> list:
    # Simple regex to find email-like strings
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return list(set(emails)) # Return unique emails

# Helper function to update internal list of team members (used by main.py)
def update_team_members(new_emails: list):
    global current_team_members
    for email in new_emails:
        if email not in current_team_members:
            current_team_members.append(email)
            print(f"(Internal) Added '{email}' to known team members list.")

# Helper function to convert datetime objects within a structure to ISO strings
# This is crucial for passing tool results back to the LLM.
def convert_datetimes_to_iso(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, list):
        return [convert_datetimes_to_iso(elem) for elem in obj]
    elif isinstance(obj, dict):
        return {k: convert_datetimes_to_iso(v) for k, v in obj.items()}
    else:
        return obj

# NEW & IMPROVED HELPER FUNCTION: Resolve a natural language date/time string to a datetime object
def resolve_datetime_from_string(date_time_str: str, current_context_date: datetime, timezone_name: str) -> datetime:
    """
    Parses a natural language date/time string using dateparser, with a fallback for common patterns.
    """
    tz = pytz.timezone(timezone_name)

    # 1. Try dateparser first, as it's the most flexible.
    try:
        settings = {
            'RETURN_AS_TIMEZONE_AWARE': True,
            'RELATIVE_BASE': current_context_date,
            'TO_TIMEZONE': timezone_name
        }
        parsed_dt = dateparser.parse(date_time_str, settings=settings)
        if parsed_dt:
            # Ensure the final datetime is in the correct timezone, as dateparser can sometimes be inconsistent.
            parsed_dt = parsed_dt.astimezone(tz)
            print(f"(Internal) Successfully parsed '{date_time_str}' with dateparser to: {parsed_dt}")
            return parsed_dt
    except Exception as e:
        print(f"(Internal) dateparser failed with error: {e}. Trying regex fallback.")

    # 2. Fallback to regex for "next [weekday] at [time]" patterns if dateparser fails.
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


# Function to dynamically update system instruction with current info
def get_updated_system_instruction():
    # Ensure timezone is correctly imported and used
    current_datetime_aware = datetime.now(pytz.timezone(google_calendar.CALENDAR_TIMEZONE))
    formatted_datetime = current_datetime_aware.strftime("%Y-%m-%d %H:%M:%S %Z%z")

    # Dynamically update the team members list for the LLM
    team_members_str = "\n".join([f"- {member}" for member in current_team_members])

    return SYSTEM_INSTRUCTION.format(
        current_datetime=formatted_datetime,
        current_timezone=google_calendar.CALENDAR_TIMEZONE,
        team_members=team_members_str
    )

# --- Main Agent Handler ---
def handle_user_input(user_input: str):
    global conversation_history, available_slots_cache, found_restaurants_cache, current_team_members

    # Always start by updating the system instruction with current context
    updated_system_instruction = get_updated_system_instruction()

    # Initialize the model for the current turn with dynamic system instruction and tools
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', # Using the recommended working model
        tools=[
            google_calendar.check_calendar_availability,
            google_calendar.send_calendar_invite,
            restaurant_search.search_restaurants,
            google_search_tool.search
        ],
        system_instruction=updated_system_instruction
    )

    # Add user's new message to the history
    conversation_history.append({"role": "user", "parts": [user_input]})

    # Start a chat session with the updated history
    chat = model.start_chat(history=conversation_history)
    response = chat.send_message(user_input) # Send user input for current turn

    # --- THIS IS THE CRITICAL FIX FOR CONVERSATION MEMORY ---
    # The model's response, which might contain tool calls, must be added to our history log.
    # If we don't do this, the next turn will have a broken history.
    if response.candidates and response.candidates[0].content.parts:
        conversation_history.append(response.candidates[0].content)
    # --- END CRITICAL FIX ---

    # --- ENHANCED DEBUG PRINT STATEMENT (VERBOSE) ---
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
    # --- END DEBUG PRINT STATEMENT ---


    # Process the model's response (which can be text, tool calls, or both)
    while True: # Loop to handle multi-turn tool use (model calls tool, gets result, responds)
        if response.candidates and response.candidates[0].content.parts:
            # Separate parts into tool calls and text responses
            tool_call_parts = [part.function_call for part in response.candidates[0].content.parts if part.function_call]
            text_response_parts = [part.text for part in response.candidates[0].content.parts if part.text]

            if tool_call_parts:
                # If the model wants to call one or more tools, execute them and collect responses.
                tool_responses = []
                for function_call in tool_call_parts:
                    function_name = function_call.name
                    function_args = {k: v for k, v in function_call.args.items()} # Convert to regular dict

                    print(f"\n--- Model requesting Tool Call: {function_name} with args: {function_args} ---")

                    if function_name in available_tools:
                        try:
                            # --- Dynamic Argument Handling (for datetime string resolution) ---
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

                            # Execute the tool function
                            tool_result = available_tools[function_name](**function_args)
                            print(f"--- Tool Call Successful. Result: {tool_result} ---")

                            # Cache results if needed
                            if function_name == "check_calendar_availability":
                                available_slots_cache = tool_result
                            elif function_name == "search_restaurants":
                                found_restaurants_cache = tool_result

                            # Prepare successful tool response for the model.
                            # The 'response' field for the Gemini API must be a dict. We wrap list results here.
                            processed_tool_result = convert_datetimes_to_iso(tool_result)
                            response_payload = {"result": processed_tool_result}
                            tool_responses.append({"function_response": {"name": function_name, "response": response_payload}})

                        except Exception as e:
                            error_msg = f"Error executing tool {function_name}: {e}"
                            print(error_msg)
                            # For errors, return a dictionary containing the error message.
                            # This prevents the AttributeError crash.
                            tool_responses.append({"function_response": {"name": function_name, "response": {"error": error_msg}}})
                    else:
                        error_msg = f"Tool '{function_name}' not found."
                        print(error_msg)
                        tool_responses.append({"function_response": {"name": function_name, "response": {"error": error_msg}}})

                # --- THIS IS THE CRITICAL FIX ---
                # Add all tool responses to conversation history for our record
                history_entry = {"role": "tool", "parts": tool_responses}
                conversation_history.append(history_entry)

                # After executing tools, send the *parts* of the new history entry back to the model for a new response
                response = chat.send_message(history_entry['parts'])


            elif text_response_parts:
                # If the model has a text response, combine and print it
                full_text_response = " ".join(text_response_parts)
                print(f"\nAssistant: {full_text_response}")
                conversation_history.append({"role": "model", "parts": [full_text_response]})
                break # Exit loop after getting a text response

            else:
                # Fallback if no specific parts (tool calls or text) are identified
                print("\nAssistant: I processed your request but didn't generate a specific response. Is there anything else I can help with?")
                conversation_history.append({"role": "model", "parts": ["I processed your request but didn't generate a specific response. Is there anything else I can help with?"]})
                break # Exit loop

        else:
            print("\nAssistant: I'm not sure how to respond to that. Can you please rephrase or provide more details?")
            conversation_history.append({"role": "model", "parts": ["I'm not sure how to respond to that. Can you please rephrase or provide more details?"]})
            break # Exit loop