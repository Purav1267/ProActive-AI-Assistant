Proactive AI Assistant: Team Dinner Planner
This project demonstrates a sophisticated AI assistant designed to autonomously organize team dinners. It leverages Google's Generative AI (Gemini) for natural language understanding and planning, and integrates with real-world APIs (Google Calendar and Google Places) to execute multi-step tasks.

✨ Features
Natural Language Understanding: Interact with the assistant using high-level conversational language to express complex goals.

Autonomous Planning & Tool Coordination: The AI agent can break down complex requests into logical steps and intelligently decide which external tools to use (e.g., search for restaurants, check calendar availability).

Google Places API Integration (Real-time Restaurant Search):

Finds actual restaurants based on cuisine and location.

Retrieves real-time information including restaurant names, addresses, and ratings.

Google Calendar API Integration (Real-time Scheduling):

Checks common free time slots for multiple team members.

Sends out official Google Calendar invitations to all attendees for the confirmed dinner.

Multi-Turn Conversation: The assistant can ask clarifying questions if information is missing and maintain context across multiple interactions.

Proactive Assistance: Guides the user through the planning and booking process, offering suggestions and confirmations.

🚀 Getting Started
Follow these steps to set up and run the project locally.

Prerequisites
Before you begin, ensure you have the following:

Python 3.9+ installed on your system.

A Google Account to access Google Cloud Platform and Google AI Studio.

Internet connectivity for API calls.

1. Google Cloud Project Setup & API Keys
You'll need to set up a Google Cloud Project and obtain the necessary API keys and credentials.

Google Calendar API Credentials (OAuth 2.0 Client ID):

Go to the Google Cloud Console and log in with the Google account you wish to use as the sender/organizer for calendar events (e.g., puravmalik24@gmail.com).

Create a new project or select an existing one.

Navigate to "APIs & Services" > "Enabled APIs & Services".

Click "+ ENABLE APIS AND SERVICES" and enable Google Calendar API.

Go to "Credentials" > "CREATE CREDENTIALS" > "OAuth client ID".

Select "Desktop app" as the application type and give it a descriptive name (e.g., "TeamDinnerAssistant").

Click "CREATE". A dialog will appear with your client ID and client secret.

Click "DOWNLOAD JSON" and rename the downloaded file to cred1.json.

Place cred1.json in the root directory of this project (ProActive Assistant 2/).

Go to "OAuth consent screen" (also under "APIs & Services"). Ensure the "Publishing status" is "Testing".

Under "Test users", click "+ ADD USERS" and add all Google accounts you plan to use for testing (e.g., puravmalik24@gmail.com, puravmalikcse@gmail.com, puravmalikcse2@gmail.com). This is crucial to avoid Error 403: access_denied.

Google Places API Key:

In the same Google Cloud Project, navigate to "APIs & Services" > "Enabled APIs & Services".

Enable Places API (search for it under "Google Maps Platform").

Go to "Billing" in the left-hand menu. Ensure Billing is Enabled for your project. (Places API requires this, even within the free tier).

Go to "Credentials" > "CREATE CREDENTIALS" > "API Key".

Copy this API Key. (You can optionally restrict it to "Places API" for security).

Google Gemini API Key:

Go to Google AI Studio.

Create a new API key.

Copy this API Key.

Google Custom Search API Key & Custom Search Engine ID (for google_search tool):

Go to Google Cloud Console > "APIs & Services" > "Enabled APIs & Services" and enable Custom Search API.

Go to "Credentials" and create another API Key (if you don't want to reuse the Places API key).

Go to Programmable Search Engine. Click "Add new search engine".

Give it a name, and in "What to search?", enter www.google.com (to search the entire web, or specific sites if you prefer). Create it.

After creation, go to "Overview" and copy the "Search engine ID" (CX value).

Create/Update .env file:

In the root directory of this project (ProActive Assistant 2/), create a file named .env (if it doesn't exist).

Add your collected API keys to this file:

GOOGLE_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
GOOGLE_PLACES_API_KEY="YOUR_ACTUAL_PLACES_API_KEY_HERE"

Replace the placeholder values with your actual keys.

2. Project Setup & Install Dependencies
Navigate to your project directory:

cd "C:\Users\PURAV\Desktop\Project\ProActive Assistant 2"


Create a virtual environment (highly recommended):

python -m venv venv


Activate the virtual environment:

On Windows (Command Prompt): .\venv\Scripts\activate.bat

On Windows (PowerShell): .\venv\Scripts\Activate.ps1

On macOS/Linux: source venv/bin/activate

Install required Python packages:

pip install -r requirements.txt


(Ensure your requirements.txt file is up-to-date with the necessary libraries as discussed in our previous conversations.)

3. Running the Assistant
Ensure your virtual environment is active.

Run the main application:

python main.py


4. Interacting with the Assistant
When the main.py script starts, you will see a prompt You:. You can now type your commands.

First Run & Calendar Authentication:

The very first time you run main.py (or tools/google_calendar.py), a browser window will open for Google Calendar authentication. Log in with the Google account you used to set up the Calendar API credentials and grant all permissions. This will create a token.json file in your project root, allowing future runs to bypass this step.

Example Conversation Flow:

AI Assistant is ready! Type 'exit' to quit.
Initial team members: puravmalikcse@gmail.com, puravmalikcse2@gmail.com

You: Organize a celebratory team dinner for my 2-person team in Hyderabad next week Tuesday at 9pm. We want to go somewhere with great Hyderabadi biryani near our Gachibowli office. The attendees are puravmalikcse@gmail.com and puravmalikcse2@gmail.com.


(The assistant will process this, search for restaurants, check calendar availability, and then propose options.)

Assistant: Great! I found a few Hyderabadi Biryani restaurants near Gachibowli, Hyderabad, such as [Restaurant 1 Name], [Restaurant 2 Name], and [Restaurant 3 Name]. I also checked the calendars for your team and found common availability on [Slot 1 Display], [Slot 2 Display], and [Slot 3 Display]. Would you like me to book a dinner at [Restaurant 1 Name] on [First Slot Display] for everyone?


(You will then respond, confirming your choice, using the exact restaurant name and slot the assistant proposed.)

You: Yes, book dinner at [Restaurant 1 Name] on [First Slot Display].


(The assistant will then send the calendar invite and confirm.)

Assistant: The calendar invite for dinner at [Restaurant 1 Name] on [First Slot Display] has been sent to [Attendees Names]. Enjoy your dinner!


You can exit the assistant by typing exit.

📂 Project Structure
ProActive Assistant 2/
├── .env                  # Stores your API keys (PRIVATE - DO NOT SHARE OR COMMIT!)
├── cred1.json             # Google Calendar API OAuth credentials (PRIVATE - DO NOT SHARE OR COMMIT!)
├── token.json            # Google Calendar API access token (Generated on first auth - PRIVATE!)
├── requirements.txt      # Python dependencies
├── main.py               # Main entry point for the application
├── agent_logic.py        # Core logic for the AI assistant, handles LLM interaction and tool calling
├── prompts.py            # Defines the system instruction and conversational prompts for the LLM
└── tools/
    ├── __init__.py       # Makes 'tools' a Python package
    ├── google_calendar.py  # Functions for interacting with Google Calendar API
    ├── restaurant_search.py # Functions for restaurant search using Google Places API
    └── google_search.py   # Functions for general Google Search (used for date parsing)


⚠️ Important Considerations & Workarounds
API Key Security: Remember that .env, cred1.json, and token.json contain sensitive information. DO NOT share these files publicly or commit them to your GitHub repository. The .gitignore file is configured to prevent this.
