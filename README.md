# 🏆 KSU Esports Tournament Bot

A comprehensive and feature-rich Discord bot designed to manage League of Legends tournaments at Kennesaw State University (KSU). This bot integrates with the Riot Games API, Discord, Google Sheets, and SQLite to automate player management, matchmaking, stat tracking, MVP voting, and more.

---

##  Features

- **Environment Configuration** via `.env` for secure and customizable settings
- **Player Statistics Management** using SQLite and synchronized Google Sheets
- **Riot Account Integration** with real-time summoner rank fetching
- **Advanced Genetic Matchmaking System** considering rank, tier, role preferences, and team balance
- **Sequential Match ID System** (match_1, match_2, etc.) for tracking multiple matchmaking runs
- **Team Display and Announcement** with role matchups, performance metrics, and image generation
- **Export/Import Players** to/from Google Sheets with timestamp or custom sheet names
- **MVP Voting System** allowing players to vote for most valuable players
- **Role Assignment** with optimization for player preferences and team balance
- **Admin Commands** for tournament management and player oversight

---

##  Project Structure
```
ksu_Esports_Tournament/
├── common/                # Shared utilities and API functions
│   ├── cached_details.py  # Caching logic
│   ├── common_scripts.py  # Utility functions
│   ├── database_connection.py # DB connection handling
│   ├── riot_api.py        # Riot Games API integration
│   └── images/            # Image assets for team displays
├── config/                # Configuration management
│   └── settings.py        # Global settings and environment vars
├── controller/            # Discord command logic
│   ├── admin_controller.py # Admin commands
│   ├── match_making.py    # Standard matchmaking logic
│   ├── genetic_match_making.py # Advanced genetic matchmaking
│   ├── team_display_controller.py # Team display/announcement
│   ├── player_signup.py   # Player registration
│   └── [other controller files] # Various command modules
├── model/                 # Database models
│   ├── dbc_model.py       # Main database models
│   ├── button_state.py    # UI button state handling
│   └── [other model files] # Additional models
├── view/                  # UI components
│   ├── signUp_view.py     # Signup UI
│   ├── team_announcement_image.py # Team image generation
│   └── [other view files] # Various UI components
├── tournament.py          # Main bot entry point
├── web_server.py          # Simple web viewer for database
├── requirements.txt       # Python dependencies
├── google_export.md       # Google Sheets setup guide
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
- Create a `.env` file with the following fields:
```
DISCORD_APITOKEN=your_discord_bot_token
DISCORD_GUILD=your_discord_server_id
DATABASE_NAME=tournament.db
TOURNAMENT_CH=your_tournament_channel_id
FEEDBACK_CH=your_feedback_channel_id
CHANNEL_CONFIG=comma,separated,channel,names
CHANNEL_PLAYER=player_channel_id
PRIVATE_CH=private_channel_id
API_KEY=your_riot_api_key
API_URL=https://api.riotgames.com
GOOGLE_SHEET_ID=your_google_sheet_id
CELL_RANGE=Sheet1
LOL_SERVICE_PATH=service_account.json
```

### 3. Generate Discord Bot Token
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application > Bot tab > Reset Token > Copy token
- Enable "Server Members Intent" under Privileged Gateway Intents
- Paste the token into `.env` as DISCORD_APITOKEN

### 4. Obtain Server (Guild) ID
- Enable Developer Mode in Discord settings
- Right-click your server > Copy ID > Add to `.env` as DISCORD_GUILD

### 5. Riot Games API Key
- Visit [Riot Developer Portal](https://developer.riotgames.com)
- Register for a personal key 
- Add the key to `.env` as API_KEY

### 6. Google Sheets API Setup (Optional)
- Follow the instructions in `google_export.md` to set up Google Sheets integration
- This enables the `/export_players` and `/import_players` commands

### 7. Install Python Dependencies
```bash
pip install -r requirements.txt
```
Ensure you are using Python 3.8 or later.

### 8. Run the Bot
```bash
python tournament.py
```

If successful, the terminal will display: `Logged into server as [BotName]`

---

##  Command Overview

| Command | Description |
|---------|-------------|
| `/display_teams [match_id]` | Shows teams for a specific match with role assignments |
| `/announce_teams [channel] [format]` | Announces teams to a channel as text or image |
| `/run_matchmaking [players_per_game] [selection_method]` | Generates balanced teams using genetic algorithm |
| `/export_players [custom_name]` | Exports player data to Google Sheets |
| `/import_players [sheet_name]` | Imports player data from Google Sheets |
| `/simulate_volunteers [count]` | Simulates volunteers for sitting out |
| `/record_match_result [match_id] [winning_team]` | Record match results |
| `/giveaway [prize] [entries]` | Runs a giveaway raffle |
| `/lookup [tag]` | Look up player by tag |
| `/player_details [user]` | Shows player details |
| `/register [gamename] [tag]` | Register a player |
| `/pref [role1] [role2] [role3] [role4] [role5]` | Set role preferences |
| `/role` | Updates role preferences |
| `/stats [user]` | View detailed player stats and rank |
| `/help` | Display help information |

---

## Matchmaking System

The bot uses two matchmaking approaches:

### Standard Matchmaking Logic
- Basic team formation based on player tiers and roles
- Simple balancing of teams based on calculated player performance

### Genetic Algorithm Matchmaking
- Advanced matchmaking using genetic algorithms for optimal team balance
- Considers:
  - **Player Tier**: Ranked tier from Iron to Challenger
  - **Role Preferences**: Player's preferred positions
  - **Manual Tier**: Optional custom tier assignment
  - **Win Rate**: Player's win percentage
- Uses fitness functions to evaluate team balance
- Performs up to 300 generations to find optimal team compositions
- Teams are stored with sequential match IDs (match_1, match_2, etc.)

---

## Team Display & Announcement

The bot offers multiple ways to display teams:

### Text Display
- Shows team members with their ranks, roles, and assigned positions
- Provides performance metrics and role matchup information
- Available via `/display_teams` command

### Image Generation
- Creates visually appealing team matchup images
- Displays player ranks, names, and role assignments
- Shows head-to-head role matchups
- Available via `/announce_teams` command with format option

### Match Selection
- Dropdown menu to select which match to display/announce
- Supports multiple match IDs from different matchmaking runs

---

##  Google Sheets Integration

The bot can sync player data with Google Sheets:

### Export Features
- Export all player data to Google Sheets
- Choose custom sheet names or use timestamp-based naming
- Access via `/export_players [custom_name]` command

### Import Features
- Import player data from Google Sheets
- Update player information in bulk
- Access via `/import_players [sheet_name]` command

See `google_export.md` for detailed setup instructions.

---

##  Database Structure

The bot uses SQLite with the following main tables:

- **player**: Core player information
- **game**: Player game statistics
- **Matches**: Match information with sequential IDs
- **MVP_Votes**: Player MVP voting records
- **playerGameDetail**: Detailed player game information
- **Counters**: Sequential counters for match IDs

---

##  For Players

### Getting Started
1. Join the Discord server where the tournament bot is running
2. Use `/register [gamename] [tag]` to register your League of Legends account
3. Set your role preferences with `/pref [role1] [role2] [role3] [role4] [role5]`
4. Wait for tournament organizers to run matchmaking and announce teams

### Player Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/register [gamename] [tag]` | Register your LoL account | `/register Faker T1-Faker` |
| `/pref [role1] [role2] [role3] [role4] [role5]` | Set role preferences | `/pref top mid jungle adc support` |
| `/role` | Update existing role preferences | `/role` |
| `/stats [user]` | View your or another player's stats | `/stats @Username` |
| `/player_details [user]` | View detailed player information | `/player_details @Username` |
| `/lookup [tag]` | Look up a player by tag | `/lookup T1-Faker` |
| `/vote_mvp [match_id] [player]` | Vote for MVP after a match | `/vote_mvp match_1 @Username` |

### Tips for Players
- Always set your role preferences in order from most to least preferred
- Update your role preferences if they change using the `/role` command
- If you need to sit out a game, let an admin know before matchmaking starts
- Be prompt for check-ins to ensure matchmaking works properly
- Vote for MVP after each match to recognize strong performances

## 👑 For Admins

### Installation Instructions
1. Follow the Setup Instructions section above to set up the bot
2. Invite the bot to your server using the OAuth2 URL from Discord Developer Portal
3. Ensure the bot has proper permissions (manage roles, send messages, embed links, etc.)
4. Set up the required channels in your `.env` file
5. Start the bot with `python tournament.py`

### Admin-Only Commands
| Command | Description | Access |
|---------|-------------|--------|
| `/run_matchmaking [players_per_game] [selection_method]` | Start the matchmaking process | Admin only |
| `/announce_teams [channel] [format]` | Announce created teams | Admin only |
| `/display_teams [match_id]` | Display teams for a specific match | Admin only |
| `/export_players [custom_name]` | Export player data to Google Sheets | Admin only |
| `/import_players [sheet_name]` | Import player data from Google Sheets | Admin only |
| `/swap_players [match_id] [player1] [player2]` | Swap two players between teams | Admin only |
| `/record_match_result [match_id] [winning_team]` | Record match results | Admin only |
| `/set_toxicity [player] [points]` | Set toxicity points for a player | Admin only |
| `/set_tier [player] [tier]` | Manually set a player's tier | Admin only |
| `/checkin_start [time]` | Start the check-in process | Admin only |
| `/simulate_volunteers [count]` | Simulate volunteers for sitting out | Admin only |
| `/giveaway [prize] [entries]` | Run a giveaway raffle | Admin only |

### Configuration Options
All configuration is done through the `.env` file. The main options are:

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_APITOKEN` | Your Discord bot token | Yes |
| `DISCORD_GUILD` | Your Discord server ID | Yes |
| `DATABASE_NAME` | Name of the SQLite database file | Yes |
| `TOURNAMENT_CH` | Channel ID for tournament announcements | Yes |
| `FEEDBACK_CH` | Channel ID for feedback messages | Yes |
| `CHANNEL_CONFIG` | Comma-separated channel names to create | Yes |
| `CHANNEL_PLAYER` | Channel ID for player-related messages | Yes |
| `PRIVATE_CH` | Channel ID for admin-only messages | Yes |
| `API_KEY` | Riot Games API key | Yes |
| `API_URL` | Riot Games API URL | Yes |
| `GOOGLE_SHEET_ID` | Google Sheet ID for import/export | Optional |
| `CELL_RANGE` | Cell range in Google Sheet | Optional |
| `LOL_SERVICE_PATH` | Path to Google service account JSON | Optional |

## 🐛 Known Issues and Limitations

### Known Bugs
- Database locking can occur when multiple operations happen simultaneously
  - **Workaround**: Restart the bot to clear any hanging connections
- Team display may show duplicate players if multiple runs of matchmaking are done with the same match_id
  - **Fix**: Now using sequential match IDs to avoid conflicts
- Google Sheets export occasionally times out with large player pools
  - **Workaround**: Export in smaller batches or use a more stable internet connection

### Undeveloped Features
- Match history tracking and statistics over time
- Automatic team balancing based on past performance
- Integration with tournament bracket systems
- Player ranking system based on performance
- Automated match scheduling

### Compatibility and Requirements
- Requires Python 3.8 or later
- Discord.py library v2.0.0 or higher
- SQLite database (included with Python)
- Stable internet connection for Riot API and Discord connectivity
- For Google Sheets functionality: Google Cloud account and proper API setup

## 🔧 Troubleshooting Tips
- Riot API error? Verify your API key is valid and not expired
- Commands unresponsive? Check the bot log at `Log/info.log`
- Google Sheets integration not working? Verify service account setup
- Match display issues? Check that teams were properly created with `/run_matchmaking`
- Database locked errors? Restart the bot to clear any hanging connections
- Discord permission issues? Ensure the bot has proper permissions in the server

---

##  Future Development

### Planned Improvements
- Improve image generation with more customization options
- Expand Google Sheets integration for match results
- Add tournament bracket management
- Implement historical player performance tracking
- Create a web dashboard for tournament management
- Support for multiple games beyond League of Legends
- Automated match result verification

---

