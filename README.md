# 🌟 Proactive AI Assistant: Team Dinner Planner 🍽️

Welcome to the **Proactive AI Assistant**, a smart virtual agent that automates planning **team dinners** end-to-end! It leverages **Google's Gemini AI**, **Google Calendar**, and **Google Places APIs** to understand your request, find ideal venues, and schedule the event — all from a single conversational prompt.

---

## ✨ Core Features & Capabilities

### 🗣️ Natural Language Understanding
- Comprehends conversational requests like “Book a team dinner near Gachibowli next Friday”.
- Extracts:
  - 👫 Team Size
  - 📍 Location
  - 🍽️ Cuisine
  - 📆 Date & Time
  - 📧 Attendee Emails

### 🧠 Autonomous Planning & Tool Use
- Breaks down goals into smart actions.
- Calls tools only when needed (e.g., Places API for restaurants, Calendar API for scheduling).
- Smooth multi-step reasoning between components.

### 🗺️ Google Places API Integration
- Searches real restaurants by cuisine & location.
- Returns:
  - 🏢 Restaurant names
  - 📍 Addresses
  - ⭐ Ratings
  - 🍱 Cuisine types

### 📅 Google Calendar API Integration
- Checks availability across team members’ calendars.
- Sends official invites to selected slots.
- Handles timezones smartly.

### 💬 Multi-Turn Conversations
- Asks follow-ups if input is incomplete.
- Maintains memory across steps.

### 🤖 Proactive Assistant Flow
- Curates restaurant suggestions.
- Helps finalize time & venue.
- Confirms booking in Google Calendar.

---

## 🚀 Getting Started

### 🔧 Prerequisites
- Python 3.9+
- Google Account (for API setup)
- Internet connection

---

## 🛠️ Setup Instructions

### 1. 🔐 Google API Setup

#### ✅ Google Calendar API (OAuth 2.0)
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **Google Calendar API**.
3. Create credentials:
   - Type: **OAuth Client ID**
   - App: **Desktop App**
   - Download as `cred1.json`
4. Place `cred1.json` in project root.
5. Add test users under **OAuth consent screen**.

#### ✅ Google Places API
1. In the same project, enable **Places API**.
2. Make sure **Billing** is enabled.
3. Create an **API key** for Places.
4. (Optional) Restrict key to `Places API`.

#### ✅ Google Gemini API
1. Go to [Google AI Studio](https://makersuite.google.com/app).
2. Create & copy API key.

#### ✅ Google Custom Search (Optional)
1. Enable **Custom Search API** in Cloud Console.
2. Create API Key.
3. Create a Custom Search Engine at [programmablesearchengine.google.com](https://programmablesearchengine.google.com/).
4. Set to search `www.google.com`, copy CX ID.

---

### 2. 📁 Clone the Repository

```bash
git clone https://github.com/your-username/proactive-assistant.git
cd "ProActive Assistant 2"
```

---

### 3. 🧪 Virtual Environment Setup

```bash
python -m venv venv
```

Activate the environment:

```bash
# Windows PowerShell
.
.\venv\Scripts\Activate.ps1

# Windows CMD
.
.\venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

---

### 4. 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 5. 🔐 Configure Environment

Create a `.env` file in the root:

```env
GOOGLE_API_KEY="your_gemini_api_key"
GOOGLE_PLACES_API_KEY="your_places_api_key"
```

---

### 6. ▶️ Run the Assistant

```bash
python main.py
```

---

## 💬 Example Usage

```plaintext
You: Organize a celebratory team dinner for my 2-person team in Hyderabad next week Tuesday at 9pm.
We want to go somewhere with great Hyderabadi biryani near our Gachibowli office.
The attendees are puravmalikcse@gmail.com and puravmalikcse2@gmail.com.
```

The assistant will:
- 🔍 Search for top-rated biryani spots near Gachibowli.
- 📅 Check shared availability for your team.
- ✅ Ask for confirmation.
- 📧 Book the slot & send calendar invites.

---

## 📂 Project Structure

```
ProActive Assistant 2/
├── .env                  # 🔐 API keys (NOT to be committed)
├── cred1.json            # 🔐 Google OAuth credentials
├── token.json            # 🔐 Calendar token (auto-generated)
├── requirements.txt      # 📦 Dependencies
├── main.py               # 🚀 Entry point
├── agent_logic.py        # 🧠 Assistant logic & state
├── prompts.py            # 💬 Prompt templates
└── tools/
    ├── __init__.py
    ├── google_calendar.py    # 📅 Calendar integration
    ├── restaurant_search.py  # 🍽️ Places API logic
    └── google_search.py      # 🔍 Custom Search API (optional)
```

---

## 🛡️ Security & Best Practices

- `.env`, `cred1.json`, and `token.json` must **not** be shared or committed.
- Ensure `.gitignore` contains these files.
- Rotate API keys periodically for safety.
- Use a **testing** OAuth screen before publishing.

---

## 📜 License

This project is licensed under the MIT License.

---

## 🌐 Made with ❤️ for teams who love great food & great AI.
