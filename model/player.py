import sqlite3
from config import settings

DB_PATH = settings.DATABASE_NAME

class PlayerModel:
    def update_toxicity(interaction, user):
        if "<@" in user:
            user = user[2:-1]

        try:
            # Create the database connection
            dbconn = sqlite3.connect(DB_PATH)
            cur = dbconn.cursor()

            # Query to search for player by username
            query = 'SELECT player_id FROM player WHERE LOWER(user_name) = ?'
            cur.execute(query, (user,))
            data = cur.fetchone()

            # If the player is found we'll update them
            if not data:
                return False
            
            player_id = data[0]

            # Create the update statement and add a point
            query = 'UPDATE playerGameDetail SET toxicity = toxicity + 1 WHERE player_id = ?'
            cur.execute(query, (player_id,))
            dbconn.commit()         

            return True
        
        except sqlite3.Error as e:
            print(f'Database error occurred updating toxicity: {e}')
            return False

        finally:
            cur.close()
            dbconn.close()

    def vote_mvp(interaction, user):
        if "<@" in user:
            user = user[2:-1]

        try:
            # Create the database connection
            dbconn = sqlite3.connect(DB_PATH)
            cur = dbconn.cursor()

            # Query to search for player by username
            query = 'SELECT player_id FROM player WHERE LOWER(user_name) = ?'
            cur.execute(query, (user,))
            data = cur.fetchone()

            # If the player is found we'll update them
            if not data:
                return False
            
            player_id = data[0]

            # Create the update statement and add a point
            query = 'UPDATE playerGameDetail SET mvps = COALESCE(mvps, 0) + 1 WHERE player_id = ?'
            cur.execute(query, (player_id,))
            dbconn.commit()         

            return True
        
        except sqlite3.Error as e:
            print(f'Database error occurred updating MVP points: {e}')
            return False

        finally:
            cur.close()
            dbconn.close()