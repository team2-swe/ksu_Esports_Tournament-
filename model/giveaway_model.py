import random
import discord

class GiveawayModel:
    @staticmethod
    def pick_winners(result, result2, val):
        """Randomly pick winners from the filtered members."""

        #Step 1: check if the result value exist in result2
        ###then exclude\
        result_id_list = {player_id for player_id, _ in result}
        fillterd_result2 = [row for row in result2 if row[0] not in result_id_list]

        #Step 2: get the random playeres
        random_picked = random.sample(fillterd_result2, val)
        randomPicked = [pname for _, pname in random_picked]


        # topPlayerDic = dict(result)
        topPlayer = [pname for _, pname in result]

        
        return topPlayer, randomPicked
