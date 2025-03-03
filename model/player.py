import sqlite3

DB_PATH = "Tournament_DB.db"

class PlayerModel:
    def update_toxicity(interaction, user):
        if "<@" in user:
            user = user[2:-1]

        try:
            # Create the database connection
            dbconn = sqlite3.connect("Tournament_DB.db")
            cur = dbconn.cursor()

            # Var to determine if the user passed in exists
            found_user = False

            # Query to search for player by discordName or riotID
            query = 'SELECT EXISTS(SELECT discordName FROM player WHERE LOWER(discordName) = ? OR LOWER(riotID) = ? OR discordID = ?)'
            args = (user, user, user)
            cur.execute(query, args)
            data = cur.fetchone()

            # If the player is found we'll update them
            if data[0] != 0:
                # Set the return var to true since the user was found
                found_user = True

                # Create the update statement and add a point
                query = 'UPDATE Player SET toxicity = toxicity + 1 WHERE LOWER(discordName) = ? OR LOWER(riotID) = ? OR discordID = ?'
                args = (user, user, user)
                cur.execute(query, args)
                dbconn.commit()         

            return found_user
        except sqlite3.Error as e:
            print (f'Database error occurred updating toxicity: {e}')
            return e

        finally:
            cur.close()
            dbconn.close()