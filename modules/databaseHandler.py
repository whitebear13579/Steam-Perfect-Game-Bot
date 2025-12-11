import json
import os
from typing import Optional, List
from modules.logHandler import loggingHandler as log

DB_PATH = os.path.join('db', 'lastQuery.json')

def loadLastQuery(debugMode: bool = False) -> Optional[List[dict]]:
    """
    從資料庫載入上次查詢結果
    
    Args:
        debugMode: debug mode is opened or not
    
    Returns:
        list of games from last query, None if failed
    """
    try:
        if not os.path.exists(DB_PATH):
            log(3, "\"lastQuery.json\" not existed.")
            return None
        
        with open(DB_PATH, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            if not content:
                log(3, "\"lastQuery.json\" is empty, treating as new file.")
                return None
            
            data = json.loads(content)
            if not data:
                log(3, "\"lastQuery.json\" without any data.")
                return None
            
            log(2, "Successfully loaded last query result from database.")
            log(5, f"Loaded {len(data)} games from database.", debugMode)
            return data
            
    except Exception as e:
        log(4, "Error occurred while loading query data from database\n(may be the json file is broken? try to delete it and the program will automatically create a new one.)", str(e))
        return None

def saveLastQuery(gamesList: List[dict], debugMode: bool = False) -> bool:
    """
    儲存查詢結果到資料庫
    
    Args:
        gamesList: player's steam games list
        debugMode: debug mode is opened or not
    
    Returns:
        bool, whether saving was successful
    """
    try:
        with open(DB_PATH, 'w', encoding='utf-8') as file:
            json.dump(gamesList, file, ensure_ascii=False, indent=2)
        log(2, "The Database has been updated.")
        log(5, f"Saved {len(gamesList)} games to database.", debugMode)
        return True
    except Exception as e:
        log(4, "Error occurred while attempting to write to database.", str(e))
        return False

def compareGameLists(lastPrefectGames: List[dict], nowPrefectGames: List[dict], debugMode: bool = False) -> tuple:
    """
    比較新舊全成就遊戲列表的差異
    
    Args:
        lastPrefectGames: a list, the previous full prefect games
        nowPrefectGames: a list, the current full prefect games
        debugMode: debug mode is opened or not
    
    Returns:
        a tuple with two lists.
        (noLongerPrefect, newPrefectGame) - list of games no longer prefect, list of newly prefect games
    """
    noLongerPrefect = []
    newPrefectGame = []
    
    for lastGame in lastPrefectGames:
        prefectFlag = False
        nowCheckID = lastGame['appid']
        for nowGame in nowPrefectGames:
            appid = nowGame['appid']
            if nowCheckID == appid:
                prefectFlag = True
                break
        
        if not prefectFlag:
            noLongerPrefect.append(lastGame)
    
    for nowGame in nowPrefectGames:
        newFlag = True
        nowCheckID = nowGame['appid']
        for lastGame in lastPrefectGames:
            appid = lastGame['appid']
            if nowCheckID == appid:
                newFlag = False
                break
        
        if newFlag:
            newPrefectGame.append(nowGame)
    
    log(5, "The new full prefect game and no longer prefect game process completed.", debugMode)
    return (noLongerPrefect, newPrefectGame)
