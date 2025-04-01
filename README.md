
---

# 🏆 KSU Esports Tournament Bot

A powerful, feature-rich Discord bot for managing League of Legends tournaments at Kennesaw State University (KSU). This bot integrates with the Riot Games API, Discord, Google Sheets, and SQLite to automate player management, matchmaking, stat tracking, MVP voting, and more.

---

## 🚀 Features

- 🔧 **Configuration via `.env`** for sensitive tokens and file paths
- 📊 **Player stats management** using SQLite + Google Sheets sync
- 🎮 **Riot account linking** and real-time rank retrieval
- 🤖 **Dynamic matchmaking** based on rank, tier, and role preferences
- 👥 **Check-in system** and volunteer-based seating management
- 🧾 **Role preferences** through interactive dropdown UI
- 📈 **Live stat updates**, MVP voting, toxicity management
- 🛠 **Admin tools** for resets, win reporting, point updates
- 💬 **In-app help menu** with pagination

---

## 📁 Project Structure

```
ksu_Esports_Tournament/
│
├── cogs/                  # Discord command modules
├── data/                  # Database and Google Sheets sync
├── utils/                 # Utility functions
├── main.py                # Bot startup script
├── .env                   # Environment config (not included)
├── requirements.txt       # Python dependencies
└── README.md              # Project overview
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ksu_Esports_Tournament.git
cd ksu_Esports_Tournament
```

### 2. Environment Configuration

Create a `.env` file in the root directory with the following structure:

```
DISCORD_TOKEN=your_discord_bot_token
RIOT_API_KEY=your_riot_api_key
GUILD_ID=your_discord_server_id
WELCOME_CHANNEL_ID=welcome_channel_id
SPREADSHEET_PATH=path_to_google_sheet
DB_PATH=path_to_sqlite_db
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Bot

```bash
python main.py
```

---

## 🧠 Bot Commands Overview

| Command | Description |
|--------|-------------|
| `/link` | Link Riot account with Discord |
| `/rolepreference` | Set your role preference (Top, Jungle, etc.) |
| `/checkin` | Mark yourself as participating |
| `/sitout` | Volunteer to sit out a match |
| `/matchmake` | Start matchmaking for balanced teams |
| `/stats` | View personal stats |
| `/win` | Update match winner stats (admin only) |
| `/points` | Update participation points (admin only) |
| `/votemvp` | Vote for the MVP |
| `/resetdb` | Reset player stats (admin only) |
| `/help` | Show help menu with command info |

---

## 🧠 Matchmaking Logic

Teams are built based on:

- 📊 **Rank** (from Riot API)
- ⭐ **Tier** (manual assignment)
- 🎯 **Role Preferences**

