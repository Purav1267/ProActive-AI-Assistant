# tools/google_calendar.py
# This module provides an interface to interact with the Google Calendar API.
# It includes functions for authenticating the user, checking for available time slots
# across multiple calendars, and sending calendar invitations.

import os
import pytz
import dateparser
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

# --- Configuration ---

# SCOPES define the level of access requested from the user's Google account.
# If these are changed, the user's token.json must be deleted to re-authenticate.
SCOPES = ['https://www.googleapis.com/auth/calendar'] 

# A fixed timezone is used for all date/time operations to ensure consistency.
CALENDAR_TIMEZONE = 'Asia/Kolkata' 

# Global variable to hold the calendar service object after authentication.
calendar_service = None

# --- Authentication ---

def get_calendar_service():
    """
    Authenticates with the Google Calendar API using the OAuth 2.0 protocol.
    - It first tries to load existing credentials from `token.json`.
    - If credentials are not found, are invalid, or have expired, it initiates
      the OAuth flow using `cred1.json` (the client secrets file).
    - The user will be prompted to authorize access in their browser.
    - New credentials (or refreshed ones) are saved back to `token.json`.
    
    Returns:
        An authorized Google Calendar API service object, or None if authentication fails.
    """
    global calendar_service
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                print(f"Token refresh failed with invalid_grant or similar: {e}. Deleting 'token.json' and re-authenticating...")
                try:
                    os.remove('token.json')
                except FileNotFoundError:
                    pass
                if not os.path.exists('cred1.json'):
                    print("Error: 'cred1.json' not found. This file is required for authentication.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file('cred1.json', SCOPES)
                creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
            except Exception as e:
                print(f"Unexpected error during token refresh: {e}. Deleting 'token.json' and re-authenticating...")
                try:
                    os.remove('token.json')
                except FileNotFoundError:
                    pass
                if not os.path.exists('cred1.json'):
                    print("Error: 'cred1.json' not found. This file is required for authentication.")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file('cred1.json', SCOPES)
                creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        else:
            if not os.path.exists('cred1.json'):
                print("Error: 'cred1.json' not found. This file is required for authentication.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('cred1.json', SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        print("Google Calendar service initialized successfully.")
        return service
    except HttpError as error:
        print(f'An HTTP error occurred during calendar service initialization: {error}')
        return None
    except Exception as e:
        print(f"An unexpected error occurred during calendar service initialization: {e}")
        return None

# Do not initialize the service at import time to avoid auth prompts/crashes on import.
# The host application (e.g., Streamlit app) should call get_calendar_service() explicitly.


# --- Core Tool Functions ---

def check_calendar_availability(team_members_emails: list, search_start_dt: datetime, search_end_dt: datetime,
                                slot_duration_minutes: int = 120) -> list:
    """
    Finds common free time slots for a group of people.
    1. It queries the `freebusy` endpoint of the Google Calendar API to get all busy
       intervals for the specified calendars.
    2. It merges all busy intervals into a single timeline.
    3. It then iterates through the desired time window (from `search_start_dt` to 
       `search_end_dt`) in 30-minute increments, checking for slots of the
       specified `slot_duration_minutes` that do not overlap with any busy time.
    
    Args:
        team_members_emails: A list of emails to check. 'primary' is added automatically.
        search_start_dt: The start of the time window to search within (timezone-aware).
        search_end_dt: The end of the time window to search within (timezone-aware).
        slot_duration_minutes: The desired length of the free slot in minutes.

    Returns:
        A list of up to 3 available slots. Each slot is a dictionary containing a
        user-friendly display string and the start/end datetime objects. Returns an
        empty list on error or if no slots are found.
    """
    if not calendar_service:
        print("Calendar service not available. Cannot check availability.")
        return []

    # Prepare the request body for the freebusy API call.
    items = [{'id': email} for email in team_members_emails]
    if 'primary' not in [item['id'] for item in items]:
        items.append({'id': 'primary'})

    body = {
        "timeMin": search_start_dt.isoformat(),
        "timeMax": search_end_dt.isoformat(),
        "timeZone": CALENDAR_TIMEZONE,
        "items": items
    }

    try:
        # Execute the freebusy query.
        response = calendar_service.freebusy().query(body=body).execute()
        
        # Collect and merge all busy intervals from all specified calendars.
        all_busy_intervals = []
        for data in response['calendars'].values():
            for busy_slot in data.get('busy', []):
                start = dateparser.parse(busy_slot['start']).astimezone(pytz.timezone(CALENDAR_TIMEZONE))
                end = dateparser.parse(busy_slot['end']).astimezone(pytz.timezone(CALENDAR_TIMEZONE))
                all_busy_intervals.append((start, end))
        
        all_busy_intervals.sort()

        merged_busy_intervals = []
        if all_busy_intervals:
            current_start, current_end = all_busy_intervals[0]
            for i in range(1, len(all_busy_intervals)):
                next_start, next_end = all_busy_intervals[i]
                if next_start <= current_end:
                    current_end = max(current_end, next_end)
                else:
                    merged_busy_intervals.append((current_start, current_end))
                    current_start, current_end = next_start, next_end
            merged_busy_intervals.append((current_start, current_end))

        common_free_slots = []
        potential_slot_start = search_start_dt
        while potential_slot_start + timedelta(minutes=slot_duration_minutes) <= search_end_dt:
            potential_slot_end = potential_slot_start + timedelta(minutes=slot_duration_minutes)
            is_free = True
            for busy_start, busy_end in merged_busy_intervals:
                if not (potential_slot_end <= busy_start or potential_slot_start >= busy_end):
                    is_free = False
                    break
            
            if is_free:
                common_free_slots.append((potential_slot_start, potential_slot_end))
            
            potential_slot_start += timedelta(minutes=30)

        # Format the found slots for the LLM.
        formatted_and_raw_slots = []
        for start_dt, end_dt in common_free_slots[:3]: # Limit to top 3 results
            formatted_and_raw_slots.append({
                "display": f"{start_dt.strftime('%A, %B %d, %I:%M %p')} - {end_dt.strftime('%I:%M %p')}",
                "start_datetime": start_dt,
                "end_datetime": end_dt
            })
        
        return formatted_and_raw_slots
        
    except HttpError as error:
        print(f'An HTTP error occurred during free/busy query: {error}')
        return []
    except Exception as e:
        print(f"An unexpected error occurred in check_calendar_availability: {e}")
        return []


def send_calendar_invite(restaurant_name: str, address: str, slot_datetime_start: datetime,
                         slot_datetime_end: datetime, attendees_emails: list, description: str = None) -> bool:
    """
    Creates and sends a Google Calendar invitation to a list of attendees.

    Args:
        restaurant_name: The name of the restaurant for the event summary.
        address: The location of the event.
        slot_datetime_start: The start datetime of the event (timezone-aware).
        slot_datetime_end: The end datetime of the event (timezone-aware).
        attendees_emails: A list of email addresses for the attendees.
        description: An optional description for the event body.

    Returns:
        True if the event was created successfully, False otherwise.
    """
    if not calendar_service:
        print("Calendar service not available. Cannot send invite.")
        return False

    # Construct the event body for the API call.
    event = {
        'summary': f'Team Dinner at {restaurant_name}',
        'location': address,
        'description': description or 'A celebratory team dinner arranged by your AI Assistant!',
        'start': {'dateTime': slot_datetime_start.isoformat(), 'timeZone': CALENDAR_TIMEZONE},
        'end': {'dateTime': slot_datetime_end.isoformat(), 'timeZone': CALENDAR_TIMEZONE},
        'attendees': [{'email': email} for email in attendees_emails],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }

    try:
        # Insert the event into the primary calendar of the authenticated user.
        # `sendUpdates='all'` ensures that email invitations are sent to attendees.
        created_event = calendar_service.events().insert(
            calendarId='primary', body=event, sendUpdates='all'
        ).execute()
        print(f'Event created successfully: {created_event.get("htmlLink")}')
        return True
    except HttpError as error:
        print(f'An HTTP error occurred during event creation: {error}')
        return False
    except Exception as e:
        print(f"An unexpected error occurred in send_calendar_invite: {e}")
        return False

# --- Standalone Test Block ---

if __name__ == '__main__':
    # This block allows for testing the module's functions independently from the main agent.
    # It demonstrates how to call the functions and can be used for debugging.
    print("--- Running Google Calendar Tool Test ---")
    
    if not calendar_service:
        print("Calendar service did not initialize. Check credentials and permissions.")
    else:
        # Example: Check availability for a test user for the upcoming week.
        test_team_emails = ["puravmalikcse@gmail.com"]
        now = datetime.now(pytz.timezone(CALENDAR_TIMEZONE))
        
        days_until_monday = (0 - now.weekday() + 7) % 7
        next_monday = now + timedelta(days=days_until_monday)
        
        test_search_start = next_monday.replace(hour=17, minute=0, second=0)
        test_search_end = test_search_start + timedelta(days=4, hours=5)

        print(f"\nChecking availability for {test_team_emails} from {test_search_start.isoformat()} to {test_search_end.isoformat()}")
        available_slots = check_calendar_availability(test_team_emails, test_search_start, test_search_end)

        if available_slots:
            print("\nFound available slots:")
            for slot in available_slots:
                print(f"- {slot['display']}")
            
            # Example: Send a test invite for the first found slot.
            if input("\nSend a test invite for the first slot? (yes/no): ").lower() == 'yes':
                first_slot = available_slots[0]
                send_calendar_invite(
                    "Test Cafe", 
                    "456 Test Ave, Hyderabad", 
                    first_slot['start_datetime'], 
                    first_slot['end_datetime'], 
                    test_team_emails,
                    "This is a test event created for debugging purposes."
                )
        else:
            print("\nNo common available slots were found in the test window.")