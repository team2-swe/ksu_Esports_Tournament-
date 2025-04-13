# 🏆 KSU Esports Tournament Bot

A comprehensive and feature-rich Discord bot designed to manage League of Legends tournaments at Kennesaw State University (KSU). This bot integrates with the Riot Games API, Discord, Google Sheets, and SQLite to automate player management, matchmaking, stat tracking, MVP voting, and more.

---

## 🚀 Features

- **Environment Configuration** via `.env` for secure and customizable settings
- **Player Statistics Management** using SQLite and synchronized Google Sheets
- **Riot Account Integration** with real-time summoner rank fetching
- **Advanced Matchmaking System** considering rank, tier, and role preferences
- **Check-In and Sit-Out Role Buttons** for active and passive participation
- **Role Preferences Selection UI** with dropdowns
- **Live Match Data**, MVP voting, and anti-toxicity tracking
- **Comprehensive Admin Tools** including win, point, and database controls
- **Paginated In-App Help Menu** for user guidance

---

## 📁 Project Structure
```
ksu_Esports_Tournament/
├── cogs/                  # Discord command modules
├── data/                  # Database and spreadsheet sync
├── utils/                 # Helper utilities
├── main.py                # Main bot entry point
├── .env.template          # Template for environment configuration
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/your-org/ksu_Esports_Tournament.git
cd ksu_Esports_Tournament
```

### 2. Environment Configuration
- Rename `.env.template` to `.env`
- Fill in the required fields:
```
DISCORD_TOKEN=your_discord_bot_token
RIOT_API_KEY=your_riot_api_key
GUILD_ID=your_discord_server_id
WELCOME_CHANNEL_ID=channel_id_or_blank
SPREADSHEET_PATH=PlayerStats.xlsx
DB_PATH=main_db.db
```

### 3. Generate Discord Bot Token
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application > Bot tab > Reset Token > Copy token
- Enable "Server Members Intent" under Privileged Gateway Intents
- Paste the token into `.env`

### 4. Obtain Server (Guild) ID
- Enable Developer Mode in Discord settings
- Right-click your server > Copy ID > Add to `.env` as GUILD_ID

### 5. Set Spreadsheet & Database Paths
- Defaults:
```
SPREADSHEET_PATH=PlayerStats.xlsx
DB_PATH=main_db.db
```
Ensure these files exist or are renamed appropriately.

### 6. Riot Games API Key
- Visit [Riot Developer Portal](https://developer.riotgames.com)
- Register for a personal key or use the temporary development key (expires in 24 hours)
- Add the key to `.env` under RIOT_API_KEY

### 7. Install Python Dependencies
```bash
pip install -r requirements.txt
```
Ensure you are using Python 3.12.6 or later.

### 8. Run the Bot
```bash
python main.py
```

If successful, the terminal will display: `Logged in as [BotName]`

---

## 🚧 Docker Setup (Optional)
```bash
docker build -t ksu-esports-bot .
docker run -d --name ksu-esports-bot-container --env-file .env ksu-esports-bot
```
> Docker support is limited and requires further testing. Designed for use with Docker Desktop (AMD64).

---

## 🧠 Command Overview

| Command | Description |
|---------|-------------|
| `/link` | Link Riot account to Discord user |
| `/rolepreference` | Choose preferred League roles |
| `/checkin` | Join the matchmaking queue |
| `/sitout` | Volunteer to skip a match |
| `/matchmake` | Generate balanced match lobbies |
| `/stats [user]` | View detailed player stats and rank |
| `/votemvp [user]` | Initiate MVP voting session |
| `/points` | Award participation points (admin only) |
| `/win` | Assign match victory to team (admin only) |
| `/resetdb` | Reset all tracked tournament data (owner only) |
| `/unlink` | Remove user record from database (admin only) |
| `/toxicity` | Penalize unsportsmanlike behavior (admin only) |
| `/help` | Display interactive help menu |

---

## 📊 Matchmaking Logic
- Teams are formed based on:
  - **Rank**: pulled from Riot API
  - **Tier**: customized groupings in `.env`
  - **Role Preferences**: 1-5 scale, per user
- Matchmaking logic is configurable with weights:
```
TIER_WEIGHT=0.7
ROLE_PREFERENCE_WEIGHT=0.3
```
- Up to 3 lobbies can be generated simultaneously
- Player pairing randomized for each `/matchmake` use

---

## 📖 User Experience
- Bot sends welcome message and instructions upon joining
- Players must run `/link` and `/rolepreference` before joining matches
- `/checkin` and `/sitout` dynamically toggle eligibility roles
- Admins finalize matches with `/win` and `/points`
- MVP voting is limited to three sessions per day

---

## 🔧 Troubleshooting Tips
- Riot API error? Set DNS to Google's servers (8.8.8.8 / 8.8.4.4)
- Commands unresponsive? Verify `.env` and token values
- Permissions issue? Ensure "Server Members Intent" is enabled and bot role is correctly placed

---

## 💭 Development Roadmap

### Immediate Priorities
- Fix matchmaking tier retrieval
- Improve MVP voting to handle multi-lobby scenarios
- Merge MVP voting, points, and win updates into single command flow

### Quality of Life Improvements
- Update Excel sheet and usernames automatically
- Add blacklist functionality for matchmaking
- Replace Administrator bot permissions with scoped ones
- Display full rank tier details in `/stats`

### Long-Term Goals
- Global command support
- Finalize Docker implementation
- Add registration form using Discord modals

---

