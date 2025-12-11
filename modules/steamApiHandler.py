import requests
from modules.logHandler import loggingHandler as log
from typing import Optional

def getPlayerProfile(steamId: str, steamApiKey: str, debugMode: bool) -> Optional[dict]:

    """
    取得玩家的 Steam Profile

    Args:
        steamId: Steam ID
        steamApiKey: Steam API Key
        debugMode: debug mode is opened or not
    Returns:
        player profile dictionary, None if failed
    """

    try:
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            'key': steamApiKey,
            'steamids': steamId
        }
        response = requests.get(url, params=params)
        log(5, response, debugMode)
        player = response.json()

        if 'response' not in player:
            log(3, "No data return from Steam API. Check your internet connection or try again later.")
            return None
        
        players = player.get('response', {}).get('players', [])
        if not players:
            log(3, "No player data found.")
            return None
            
        playerProfile = players[0]
        log(5, f"{playerProfile}", debugMode)
        return playerProfile
        
    except Exception as e:
        log(4, "Error occurred while fetching player profile from Steam API.", str(e))
        return None
