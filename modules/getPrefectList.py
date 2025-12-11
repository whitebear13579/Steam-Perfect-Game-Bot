from modules.logHandler import loggingHandler as log
import requests

def getOwnedGames(steamId: str, steamApiKey: str, debugMode: bool) -> list:
    try:
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001"
        params = {
            'key': steamApiKey,
            'steamid': steamId,
            'include_played_free_games': True,
            'include_appinfo' : True
        }
        rsp = requests.get(url, params=params)
        log(5,rsp, debugMode)
        fullData = rsp.json()
        log(5, fullData, debugMode)

        if 'response' not in fullData:
            log(3, "No data return from Steam API. Check your internt connection or try again later.")
            return []

        getGamesList = fullData.get('response',{}).get('games',[])
        log(2, "Successfully retrieved player games data from Steam API.")
        log(5, getGamesList, debugMode)
        return getGamesList

    except Exception as e:
        log(4, "Error occurred while fetching Games list from Steam API.", e)
def getPrefectGamesList( steamId: str, steamApiKey: str, debugMode: bool ) -> list:

    """
    取得玩家的全成就列表

    Args:
        steamId: Steam ID
        steamApiKey: Steam API Key
        debugMode: debug mode is opened or not
    Returns:
        list of games with full achievements
    """

    nowPrefectGames = list()
    errorCount = 0 
    try:
        fullGamesList = getOwnedGames( steamId, steamApiKey, debugMode )

        if len(fullGamesList) == 0:
            return []

        playedGamesList = [game for game in fullGamesList if (game.get('playtime_forever',0)) > 0 ]
        nowPrefectGames.clear()
        for game in playedGamesList:
            appid = game.get('appid')
            log(5,f"Now checking : {appid}", debugMode)
            url = "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
            params = {
                'appid' : appid,
                'key' : steamApiKey,
                'steamid' : steamId,
                'l' : "tchinese"
            }
            respone = requests.get(url,params=params)
            log(5,respone, debugMode)
            try:
                nowGameAchievement = respone.json()
                if 'playerstats' not in nowGameAchievement:
                    log(3, "No data return from Steam API.")
                    errorCount = errorCount + 1 
                    continue
                
                if not nowGameAchievement['playerstats'].get('success') :
                    log(3,f"Error occurred while fetching achievement data for game {appid}.")
                    errorCount = errorCount + 1 
                    continue

                fullAchievementsFlag = 1
                achievements = nowGameAchievement['playerstats'].get('achievements',[])
                if not achievements:
                    log(3,f"No achievements existed for game {appid}")
                    fullAchievementsFlag = 0
                
                for nowAchievement in achievements:
                    if ( nowAchievement["achieved"] == 0 ):
                        fullAchievementsFlag = 0
                        break
                log(5,"----------------------------[THIS GAME SEARCH END]----------------------------", debugMode)
                if fullAchievementsFlag:
                    nowPrefectGames.append(game)

            except Exception as e:
                log(4,f"Error occurred while processing achievement data for game {appid}",e)
                continue
        if ( errorCount == 0 ):
            log(2,"Successfully retrieved current full achievements games list.")
        else:
            log(2,f"Full achievements games list retrieved, but some games failed to query status: {errorCount}")
        errorCount = 0
        return nowPrefectGames 
    except Exception as e:
        log(4, "Error occurred while checking games's achievement condition.", e)