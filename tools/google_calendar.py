import os
import pytz
import dateparser
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar'] 

# Set your desired timezone for all calendar operations
CALENDAR_TIMEZONE = 'Asia/Kolkata' 

calendar_service = None # Keep this global variable definition

def get_calendar_service():
    """
    Authenticates with the Google Calendar API.
    Handles OAuth 2.0 flow, prompts user for authorization if necessary,
    and saves/loads credentials from 'token.json'.
    Returns the authenticated Google Calendar API service object.
    """
    global calendar_service # Declare that we're modifying the global variable

    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # --- IMPORTANT CHANGE HERE ---
            # Now it looks for 'cred.json' instead of 'credentials.json'
            if not os.path.exists('cred1.json'): # Check for 'cred.json'
                print("Error: 'cred.json' not found. Please ensure it's in your project root.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('cred1.json', SCOPES) # Use 'cred.json'
            # --- END IMPORTANT CHANGE ---
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)
        print("Google Calendar service initialized successfully.")
        return service
    except HttpError as error:
        print(f'An HTTP error occurred during calendar service initialization: {error}')
        print("Please check your network connection, API key, and Google Cloud project setup.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during calendar service initialization: {e}")
        return None

# Ensure the calendar service is initialized when the module is loaded
calendar_service = get_calendar_service()


def check_calendar_availability(team_members_emails: list, search_start_dt: datetime, search_end_dt: datetime,
                                slot_duration_minutes=120):
    """
    Checks common free slots for a list of team members within a given time range.
    This is a simplified and more robust implementation.
    """
    if not calendar_service:
        print("Calendar service not available. Cannot check availability.")
        return []

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
        response = calendar_service.freebusy().query(body=body).execute()
        
        all_busy_intervals = []
        for calendar_id, data in response['calendars'].items():
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

        formatted_and_raw_slots = []
        for start_dt, end_dt in common_free_slots[:3]:
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


def send_calendar_invite(restaurant_name: str, address: str, slot_datetime_start: datetime, # Use datetime (class) directly
                         slot_datetime_end: datetime, attendees_emails: list, description: str = None): # Use datetime (class) directly
    """
    Creates and sends a Google Calendar invitation.
    Args:
        restaurant_name (str): The name of the restaurant.
        address (str): The address of the restaurant.
        slot_datetime_start (datetime): The start datetime of the event (timezone-aware).
        slot_datetime_end (datetime): The end datetime of the event (timezone-aware).
        attendees_emails (list): A list of email addresses of attendees.
        description (str, optional): A description for the event. Defaults to None.
    Returns:
        bool: True if the event was created successfully, False otherwise.
    """
    if not calendar_service:
        print("Calendar service not available. Cannot send invite.")
        return False

    event_summary = f'Team Dinner at {restaurant_name}'
    event_description = description if description else 'A celebratory team dinner arranged by AI Assistant!'

    # --- CRITICAL CHANGE FOR TESTING ATTENDEES ---
    # For this critical test, we will explicitly set the only attendee as the primary calendar.
    # This bypasses any potential issues with other email addresses.
    attendees_list_for_api = [{'email': email} for email in attendees_emails] 
    # The 'sendUpdates=all' is what sends the actual email. Let's keep it.
    # --- END CRITICAL CHANGE ---

    event = {
        'summary': event_summary,
        'location': address,
        'description': event_description,
        'start': {
            'dateTime': slot_datetime_start.isoformat(),
            'timeZone': CALENDAR_TIMEZONE,
        },
        'end': {
            'dateTime': slot_datetime_end.isoformat(),
            'timeZone': CALENDAR_TIMEZONE,
        },
        'attendees': attendees_list_for_api, # Use our simplified list here
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60}, # Email reminder 24 hours before
                {'method': 'popup', 'minutes': 10},     # Popup reminder 10 minutes before
            ],
        },
    }

    try:
        # 'calendarId': 'primary' refers to the default calendar of the authenticated user.
        # 'sendUpdates': 'all' sends notifications to attendees.
        event = calendar_service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()
        print(f'Event created: {event.get("htmlLink")}')
        return True
    except HttpError as error:
        print(f'An HTTP error occurred during event creation: {error}')
        print("Please ensure attendees' emails are valid and your calendar permissions are correct.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred in send_calendar_invite: {e}")
        return False

# --- Example Usage (for testing this module independently) ---
if __name__ == '__main__':
    print("--- Running Google Calendar Tool Test ---")
    
    if not calendar_service:
        print("Calendar service did not initialize. Please check credentials.json and network.")
    else:
        # Use the primary authenticated email for testing, as a confirmed valid email.
        # This is crucial to get past the "Invalid attendee email" error.
        test_team_emails = ["puravmalikcse@gmail.com"] 
        # Once this works, you can try adding puravmalikcse@gmail.com and puravmalikcse2@gmail.com back,
        # but the error might reappear if Google's API still deems them invalid for invite.

        now = datetime.now(pytz.timezone(CALENDAR_TIMEZONE)) 
        
        # Calculate next Monday
        days_until_monday = (0 - now.weekday() + 7) % 7 # 0 is Monday
        next_monday = now + timedelta(days=days_until_monday)
        
        test_search_start = next_monday.replace(hour=17, minute=0, second=0, microsecond=0) # Monday 5 PM
        test_search_end = next_monday.replace(hour=22, minute=0, second=0, microsecond=0) + timedelta(days=4) # Friday 10 PM same week

        print(f"\nChecking availability for {test_team_emails} from {test_search_start.isoformat()} to {test_search_end.isoformat()}")
        available_slots = check_calendar_availability(test_team_emails, test_search_start, test_search_end)

        if available_slots:
            print("\nAvailable common slots:")
            for slot in available_slots:
                print(f"- {slot['display']}")
            
            confirm_send = input("\nSend a test invite for the first available slot? (yes/no): ").lower()
            if confirm_send == 'yes':
                first_slot = available_slots[0]
                send_calendar_invite(
                    "Test Restaurant", 
                    "123 Test St, Hyderabad", 
                    first_slot['start_datetime'], 
                    first_slot['end_datetime'], 
                    test_team_emails, # This list is currently ignored by send_calendar_invite with the new change
                    "This is a test invite from your AI Assistant. Please ignore."
                )
        else:
            print("\nNo common available slots found for the test team within the specified time.")
            print("Please ensure your account (puravmalik24@gmail.com) has free time in its calendar for next week's evenings.")