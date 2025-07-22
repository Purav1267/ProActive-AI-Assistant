# 🌟 Proactive AI Assistant: Team Dinner Planner 🍽️

This project showcases a cutting-edge AI assistant designed to **autonomously orchestrate team dinners** from start to finish! It harnesses the power of Google's Generative AI (Gemini) for intelligent natural language understanding and complex planning, seamlessly integrating with real-world APIs (Google Calendar and Google Places) to execute multi-step tasks.

## ✨ Core Features & Capabilities

Our AI Assistant isn't just a chatbot; it's a proactive agent that can:

* **🗣️ Natural Language Understanding:**
    * Effortlessly comprehends high-level, conversational requests for organizing events.
    * Extracts all crucial details like team size, location, cuisine preferences, and attendee emails from your natural input.

* **🧠 Autonomous Planning & Tool Coordination:**
    * **Breaks down complex goals** (e.g., "organize a team dinner") into a logical sequence of actionable steps.
    * **Intelligently decides which external tools to invoke** (e.g., "search for restaurants," "check calendar availability").
    * **Manages the flow** between different API calls and user interactions.

* **🗺️ Google Places API Integration (Real-time Restaurant Search):**
    * Connects directly to the Google Places API to **find actual restaurants** based on specified cuisine (e.g., "North Indian") and precise locations (e.g., "Sector 31, Gurgaon").
    * Retrieves **real-time, accurate information** including:
        * Restaurant Names 🏢
        * Full Addresses 📍
        * User Ratings ⭐
        * Cuisine Types 🍜

* **📅 Google Calendar API Integration (Real-time Scheduling):**
    * Utilizes the Google Calendar API to **check common free time slots** across multiple team members' calendars.
    * **Sends out official Google Calendar invitations** 📧 to all confirmed attendees for the scheduled dinner.
    * Handles timezone awareness for accurate scheduling.

* **💬 Multi-Turn Conversation:**
    * Engages in dynamic, multi-turn dialogues, asking **clarifying questions** if initial information is incomplete (e.g., "Do you have a preferred date and time?").
    * Maintains **context** throughout the conversation to ensure a smooth planning process.

* **🤝 Proactive Assistance:**
    * Guides the user through the entire dinner planning and booking process.
    * Offers **curated suggestions** (e.g., "Would you like me to book a table at X restaurant on Y date?").
    * Provides **clear confirmations** once actions are completed.

## 🚀 Getting Started: Set Up Your AI Assistant!

Follow these detailed steps to get your Proactive AI Assistant up and running on your local machine.

### Prerequisites

Before you begin, make sure you have:

* **Python 3.9+** installed on your operating system. 🐍
* **A Google Account** to access Google Cloud Platform and Google AI Studio. 🔑
* **Stable Internet connectivity** for all API calls. 🌐
* **Git** installed on your system for cloning the repository.

## 1. Clone the Repository

First, clone this GitHub repository to your local machine:

```bash
git clone https://github.com/Purav1267/ProActive-AI-Assistant.git
cd ProActive-AI-Assistant # Navigate into the cloned directory
```
(Replace ```Purav1267``` with your actual GitHub username if the repository URL is different.)
## 2. Google Cloud Project Setup & API Keys
You'll need to configure a Google Cloud Project and obtain the necessary API keys and credentials for various services.
### 1.🔐 Google Calendar API Credentials (OAuth 2.0 Client ID):
* Navigate to the **Google Cloud Console** and log in with the Google account you wish to use as the primary sender/organizer for calendar events.
* **Create a new project** or select an existing one.
* Enable the **Google Calendar API**.
* In the left-hand menu, go to "APIs & Services" > "Enabled APIs & Services".
* Click "+ ENABLE APIS AND SERVICES" and search for, then enable, the **Google Calendar API**.
* Go to "Credentials" > "CREATE CREDENTIALS" > "OAuth client ID".
* Select "Desktop app" as the application type and give it a descriptive name (e.g., "TeamDinnerAssistant").
* Click "CREATE". A dialog will appear with your Client ID and Client Secret.
* Click "DOWNLOAD JSON" and rename the downloaded file to ```cred1.json```.
* Place this ```cred1.json``` file directly into the root directory of your cloned project.
* Go to "OAuth consent screen" (also under "APIs & Services"). Ensure the "Publishing status" is set to "Testing".
* Under the "Test users" section, click "+ ADD USERS" and add all Google accounts you plan to use for testing (e.g., ```puravmalik24@gmail.com```, ```puravmalikcse@gmail.com```, ```puravmalikcse2@gmail.com```). This step is crucial to prevent ```Error 403: access_denied``` during authentication.
### 2.📍 Google Places API Key:
* In the **same Google Cloud Project**, navigate to "APIs & Services" > "Enabled APIs & Services".
* Enable the **Places API** (search for it under "Google Maps Platform").
* Go to "Billing" in the left-hand menu. **It is essential that Billing is Enabled for your project.** (The Places API requires this, even if your usage falls within the generous free tier).
* Go to "Credentials" > "CREATE CREDENTIALS" > "API Key".
* **Copy this newly generated API Key.** (For enhanced security, you can optionally restrict its usage to only the "Places API" service).

### 3.🧠 Google Gemini API Key:
* Head over to **Google AI Studio**.
* Create a new API key for your project.
* **Copy this API Key**.

### 4.🔍 Google Custom Search API Key & Search Engine ID(for **google_search** tool):
* In the Google Cloud Console, go to "APIs & Services" > "Enabled APIs & Services" and enable the **Custom Search API**.
* Go to "Credentials" and create another API Key (you can reuse an existing one if you prefer, but a dedicated one is cleaner).
* Visit the Programmable Search Engine website. Click "Add new search engine".
* Provide a name for your search engine. In the "What to search?" field, enter **www.google.com** to allow it to search the entire web (or specific domains if you have a narrower scope). Create the search engine.
* After creation, go to the "Overview" section and copy the "Search engine ID" (this is your CX value).

### 5.📄 Create/Update `.env` file:
* In the root directory of your cloned project, create a file named `.env` (if it doesn't already exist).
* Add your collected API keys to this file. **Remember to replace the placeholder values with your actual keys!**

```env
GOOGLE_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
GOOGLE_PLACES_API_KEY="YOUR_ACTUAL_PLACES_API_KEY_HERE"
```

---

## 3. Install Dependencies
  ### 1.Create a virtual environment (highly recommended for dependency isolation):
```bash
cd "C:\Users\PURAV\Desktop\Project\ProActive Assistant 2"
python -m venv venv
```

### 2. Activate Environment:

- **Windows (CMD)**: `.\venv\Scripts\activate.bat`
- **Windows (PowerShell)**: `.venv\Scripts\Activate.ps1`
- **macOS/Linux**: `source venv/bin/activate`

### 3. Install required Python packages:
* Ensure your `requirements.txt` file is up-to-date with all necessary libraries.
* Run the installation command:
```bash
pip install -r requirements.txt
```

---

## 4. Running the Assistant
You have two ways to run the assistant: via the Command Line Interface (CLI) or via the Streamlit web application.


A. **Running via Command Line Interface (CLI)**
1. Ensure your virtual environment is active.

2. Launch the main CLI application:

```Bash

python main.py
```

B. **Running via Streamlit Web Application (Local Host)**
1. Ensure your virtual environment is active.

2. Launch the Streamlit application:

```Bash

streamlit run app.py
```
This command will open a new tab in your web browser (usually at `http://localhost:8501`) displaying the chat interface.
 1. Ensure your virtual environment is active.
 2. Launch the main application:
```bash
python main.py
```

---

## 5. Interacting with the Assistant
When the `main.py` script starts, you will see a prompt `You:`. You can now type your commands and interact with the AI Assistant.
**First Run & Calendar Authentication:**
- The very first time you run` main.py` (or `tools/google_calendar.py` directly), a browser window will open for Google Calendar authentication. Log in with the Google account you used to set up the Calendar API credentials and grant all necessary permissions. This will create a `token.json` file in your project root, allowing future runs to bypass this browser step.

**Example Conversation Flow:**

```text
AI Assistant is ready! Type 'exit' to quit.
Initial team members: puravmalikcse@gmail.com, puravmalikcse2@gmail.com

You: Organize a celebratory team dinner for my 2-person team in Hyderabad next week Tuesday at 9pm. We want to go somewhere with great Hyderabadi biryani near our Gachibowli office. The attendees are puravmalikcse@gmail.com and puravmalikcse2@gmail.com.
```
(The assistant will process this, search for restaurants using Google Places, check calendar availability using Google Calendar, and then propose curated options.)

```text
Assistant: Great! I found a few Hyderabadi Biryani restaurants near Gachibowli, Hyderabad, such as [Restaurant 1 Name], [Restaurant 2 Name], and [Restaurant 3 Name]. I also checked the calendars for your team and found common availability on [Slot 1 Display], [Slot 2 Display], and [Slot 3 Display]. Would you like me to book a dinner at [Restaurant 1 Name] on [First Slot Display] for everyone?
```
(You will then respond, confirming your choice, using the exact restaurant name and slot the assistant proposed.)
```text
You: Yes, book dinner at [Restaurant 1 Name] on [First Slot Display].
```
(The assistant will then send the calendar invite and confirm the booking.)

```text
Assistant: The calendar invite for dinner at [Restaurant 1 Name] on [First Slot Display] has been sent to [Attendees Names]. Enjoy your dinner!
```
You can exit the assistant at any time by typing `exit`.
## 📂 Project Structure

```
ProActive Assistant 2/
├── .env                  # 🔑 Stores your API keys (PRIVATE)
├── cred1.json            # 🔐 Google Calendar API OAuth credentials (PRIVATE)
├── token.json            # 🔒 Google Calendar API access token (PRIVATE)
├── requirements.txt      # 📦 Python dependencies
├── main.py               # ▶️ Main entry point
├── agent_logic.py        # 🧠 Core assistant logic
├── prompts.py            # 📜 LLM system prompts
└── tools/                # 🛠️ External integrations
    ├── __init__.py
    ├── google_calendar.py    # 📅 Google Calendar
    ├── restaurant_search.py  # 🍽️ Google Places
    └── google_search.py      # 🔍 Google Search
```

---

## ⚠️ Important Considerations & Workarounds

- **API Key Security**: NEVER share `.env`, `cred1.json`, or `token.json` publicly.
- **OAuth Testing Mode**: Make sure your Google OAuth is in testing mode with proper test users.
