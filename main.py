import requests
import time
from configparser import ConfigParser
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import tasks
import json
import os
import random

#setting Logger
istime = time.localtime()
isname = time.strftime("%Y-%m-%d %I：%M：%S：%p",istime)

if not os.path.exists('./log'):
    os.makedirs('./log')
    print("Info > log folder not existed, create a new one.")

if not os.path.exists('./db'):
    os.makedirs('./db')
    print("Info > db folder not existed, create a new one.")

print("Info > Folder integrity check completed.")


rootLogger = logging.getLogger()
handler = logging.FileHandler(f'./log/Log-{isname}.log','w','utf-8')
rootLogger.addHandler(handler)

#handle the congfig settings
conf = ConfigParser()
try:
    conf.read('config.ini', encoding='utf-8')
    SteamAPIKey = conf['General']['STEAM_API_KEY']
    SteamID = conf['General']['STEAMID64']
    Broadcast = conf.getint('General','BOARDCAST_CHANNEL')
    BotToken = conf['General']['BOT_TOKEN']
    UpdateFrequency = conf.getint('General','UPDATE_FREQ')
    MessageEveryLoop = conf.getboolean('General', 'MESSAGE_EVERY_LOOP')
    BotVersion = conf['Debug']['BOT_VERSION']
    DebugMode = conf.getboolean('Debug', 'DEBUG_MODE')
    if DebugMode:
        rootLogger.setLevel(logging.DEBUG)
        print("Debug > Debug mode is set to true.")
        logging.debug("Debug > Debug mode is set to true.")
    else:
        rootLogger.setLevel(logging.INFO)
    print("Info > Settings has been read from config.ini :D")
    logging.info("Info > Settings has been read from config.ini :D")
except Exception as e:
    print("Cannot find \"config.ini\", please check your bot file is complete !")
    print(e)
    logging.error("Cannot find \"config.ini\", please check your bot file is complete !")
    logging.error(e)


#handle the all msg's Dump and logging
def logPrint(cond: int,msg, err: Optional[str] = None):
    global DebugMode
    if cond == 1:
        print(f"Term > {msg}")
    elif cond == 2:
        print(f"Info > {msg}")
        logging.info(f"Info > {msg}")
    elif cond == 3:
        print(f"Warn > {msg}")
        logging.warning(f"Warn > {msg}")
    elif cond == 4:
        print(f"Err! > {msg}")
        print(err)
        logging.error(f"Err! > {msg}")
        logging.error(err)
    elif cond == 5:
        if DebugMode:
            print(f"Debug > {msg}")
            logging.debug(f"Debug > {msg}")


nowPrefectGames = []
lastPrefectGames = []
errorCount = 0
firstUsed = 1
def getOwnedGames() -> list:
    try:
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001"
        params = {
            'key' : SteamAPIKey,
            'steamid' : SteamID,
            'include_plaeyed_free_games' : True,
            'include_appinfo' : True
        }
        respone = requests.get(url,params=params)
        logPrint(5,respone)
        fullData = respone.json()
        logPrint(5,fullData)

        if 'response' not in fullData:
            logPrint(3,"No data return from Steam API. Check your internt connection or try again later.")
            return []

        getGamesList = fullData.get('response',{}).get('games',[])
        logPrint(2,"Successfully retrieved player games data from Steam API.")
        logPrint(5,getGamesList)
        return getGamesList
    except Exception as e:
        logPrint(4,"Error occurred while fetching Games list from Steam API.",e)


def getPrefectGamesList() -> list:
    try:
        global nowPrefectGames
        global errorCount
        fullGamesList = getOwnedGames()

        if len(fullGamesList) == 0:
            return []
        
        playedGamesList = [game for game in fullGamesList if (game.get('playtime_forever',0)) > 0 ]
        nowPrefectGames.clear()
        for game in playedGamesList:
            appid = game.get('appid')
            logPrint(5,f"Now checking : {appid}")
            url = "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
            params = {
                'appid' : appid,
                'key' : SteamAPIKey,
                'steamid' : SteamID,
                'l' : "tchinese"
            }
            respone = requests.get(url,params=params)
            logPrint(5,respone)
            try:
                nowGameAchievement = respone.json()
                if 'playerstats' not in nowGameAchievement:
                    logPrint(3, "No data return from Steam API.")
                    errorCount = errorCount + 1 
                    continue
                
                if not nowGameAchievement['playerstats'].get('success') :
                    logPrint(3,f"Error occurred while fetching achievement data for game {appid}.")
                    errorCount = errorCount + 1 
                    continue

                fullAchievementsFlag = 1
                achievements = nowGameAchievement['playerstats'].get('achievements',[])
                if not achievements:
                    logPrint(3,f"No achievements existed for game {appid}")
                    fullAchievementsFlag = 0
                
                for nowAchievement in achievements:
                    if ( nowAchievement["achieved"] == 0 ):
                        fullAchievementsFlag = 0
                        break
                logPrint(5,"----------------------------[THIS GAME SEARCH END]----------------------------")
                if fullAchievementsFlag:
                    nowPrefectGames.append(game)

            except Exception as e:
                logPrint(4,f"Error occurred while processing achievement data for game {appid}",e)
                continue
        if ( errorCount == 0 ):
            logPrint(2,"Successfully retrieved current full achievements games list.")
        else:
            logPrint(2,f"Full achievements games list retrieved, but some games failed to query status: {errorCount}")
        errorCount = 0
        return nowPrefectGames   
    except Exception as e:
        logPrint(4,"Error occurred while checking games's achievement condition.",e)

#discord bot initialization
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    cmds = await tree.sync()
    logPrint(3, f"Login user : {client.user}")
    logPrint(2, f"{len(cmds)} slash commands loaded.")
    discord.VoiceClient.warn_nacl = False
    global DebugMode
    global firstUsed
    global lastPrefectGames
    global nowPrefectGames
    
    #try to load last query result (or create new)
    try:
        file_path = os.path.join('db','lastQuery.json')

        #if file not existed
        if not os.path.exists(file_path):

            if ( len(getPrefectGamesList()) == 0 ):
                logPrint(3,"The program has TERMINATED due to no data was returned from Steam API.")
                os._exit()

            logPrint(2,f"Loaded full achievements games: {len(nowPrefectGames)}")

            lastPrefectGames = nowPrefectGames
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(nowPrefectGames, file, ensure_ascii=False, indent=2)
            logPrint(3,f"\"lastQuery.json\" not existed, automatically created at db folder.")
        else:
            noContentFlag = False
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                if not content: 
                    noContentFlag = True
                    if ( len(getPrefectGamesList()) == 0 ):
                        logPrint(3,"The program has TERMINATED due to no data was returned from Steam API.")
                        os._exit()
                    logPrint(2,f"Loaded full achievements games: {len(nowPrefectGames)}")

                    logPrint(3, "\"lastQuery.json\" is empty, treating as new file.")
                else:
                    lastPrefectGames = json.loads(content)  
            if noContentFlag :
                with open(file_path,'w', encoding='utf-8') as file:
                    json.dump(nowPrefectGames, file, ensure_ascii=False, indent=2)
            
            #if file existed, but without any data
            if not lastPrefectGames:
                
                if not nowPrefectGames:
                    if ( len(getPrefectGamesList()) == 0 ):
                        logPrint(3,"The program has TERMINATED due to no data was returned from Steam API.")
                        os._exit()

                    logPrint(2,f"Loaded full achievements games: {len(nowPrefectGames)}")

                    lastPrefectGames = nowPrefectGames
                    with open(file_path, 'w', encoding='utf-8') as file:
                        json.dump(lastPrefectGames, file, ensure_ascii=False, indent=2)
                    logPrint(3,f"\"lastQuery.json\" without any data, automatically write current data.")
            else:
                channel = await client.fetch_channel(Broadcast)
                try:
                    firstUsed = 0
                    url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
                    params = {
                        'key': SteamAPIKey,
                        'steamids': SteamID
                    }
                    response = requests.get(url, params=params)
                    logPrint(5,response)
                    player = response.json()

                    if 'response' not in player:
                        logPrint(3,"No data return from Steam API. Check your internt connection or try again later.")
                    
                    player = player.get('response', {}).get('players',[])
                    playerProfile = player[0]
                    
                    logPrint(5,f"{playerProfile}")

                    embed=discord.Embed(title="已載入設定檔 <:catlove:1388792473626607676>", color=(0xffb243 if DebugMode else 0x02bc7d))
                    embed.set_author(name="工具已成功啟動", icon_url="https://i.imgur.com/QS401hJ.png")
                    embed.set_thumbnail(url=f"{playerProfile['avatarfull']}")
                    embed.add_field(name="登入使用者", value=f"{client.user}", inline=False)
                    embed.add_field(name="從本地資料庫載入的全成就遊戲列表", value=f"{len(lastPrefectGames)}", inline=False)
                    embed.add_field(name="設定查詢頻率（秒）", value=f"{UpdateFrequency}", inline=False)
                    embed.add_field(name="查詢玩家", value=f"{playerProfile['personaname']}", inline=False)
                    embed.add_field(name="查詢提示訊息", value=f"{ "開啟" if MessageEveryLoop else "關閉" }", inline=False)
                    embed.add_field(name="請稍後！", value="我們正向 Steam API 擷取新列表，若有更新馬上就通知你 <:meowok:1388816457718038660>", inline=False)
                    if DebugMode:
                        embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，這可能導致非預期的錯誤發生。", inline=False)
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😎")
                    await channel.send(embed=embed)

                    logPrint(2,f"Successfully loaded last query result in database.")
                except Exception as e:
                    embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                    embed.set_author(name="工具啟動失敗", icon_url="https://i.imgur.com/Z9nqxHg.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                    if DebugMode:
                            embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                    await channel.send(embed=embed)

                    logPrint(4, "Error occurred during initialization.",e)
    except Exception as e:
        logPrint(4,"Error occurred while loading query data from database\n(may be the json file is broken? try to delete it and the program will automactically create a new one.)",e)

    if not queryAndBroadcast.is_running():
        queryAndBroadcast.start()
        logPrint(2,f"The task has been started. Automatically refresh frequency is : {UpdateFrequency}s")

@tasks.loop(seconds = UpdateFrequency)
async def queryAndBroadcast():
    channel = await client.fetch_channel(Broadcast)
    global DebugMode
    global firstUsed
    global lastPrefectGames
    global nowPrefectGames

    if firstUsed:
        try:
            url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
            params = {
                'key': SteamAPIKey,
                'steamids': SteamID
            }
            response = requests.get(url, params=params)
            logPrint(5,response)
            player = response.json()

            if 'response' not in player:
                logPrint(3,"No data return from Steam API. Check your internt connection or try again later.")
            
            player = player.get('response', {}).get('players',[])
            playerProfile = player[0]
            lastPrefectGames = nowPrefectGames

            embed=discord.Embed(title="已載入設定檔 <:catlove:1388792473626607676>", color=(0xffb243 if DebugMode else 0x02bc7d))
            embed.set_author(name="工具初始化完成！", icon_url="https://i.imgur.com/QS401hJ.png")
            embed.set_thumbnail(url=f"{playerProfile['avatarfull']}")
            embed.add_field(name="登入使用者", value=f"{client.user}", inline=False)
            embed.add_field(name="已載入全成就遊戲", value=f"{len(lastPrefectGames)}", inline=False)
            embed.add_field(name="設定查詢頻率（秒）", value=f"{UpdateFrequency}", inline=False)
            embed.add_field(name="查詢玩家", value=f"{playerProfile['personaname']}", inline=False)
            embed.add_field(name="查詢提示訊息", value=f"{ "開啟" if MessageEveryLoop else "關閉" }", inline=False)
            if DebugMode:
                embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，這可能導致非預期的錯誤發生。", inline=False)
            embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😎")
            await channel.send(embed=embed)

            logPrint(2,"Initialization completed, FIRST USED Mode.")
            firstUsed = False
        except Exception as e:
            embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
            embed.set_author(name="初始化失敗", icon_url="https://i.imgur.com/Z9nqxHg.png")
            embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
            if DebugMode:
                    embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
            await channel.send(embed=embed)
            logPrint(4, "Error occurred during initialization.",e)
    else:
        if not lastPrefectGames:
            err = f"{lastPrefectGames} list is empty!"

            embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{err}", color=0xff5e43)
            embed.set_author(name="列表為空", icon_url="https://i.imgur.com/Z9nqxHg.png")
            embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
            if DebugMode:
                    embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
            await channel.send(embed=embed)

            logPrint(4,"Error occurred due to the full achievements list is empty.",err)
        else:
            noLongerPrefect = []
            newPrefectGame = []
            getPrefectGamesList()
            for lastGame in lastPrefectGames:
                prefectFlag = 0
                nowCheckID = lastGame['appid']
                for nowGame in nowPrefectGames:
                    appid = nowGame['appid'] 
                    if nowCheckID == appid:
                        prefectFlag = 1
                
                if not prefectFlag:
                    noLongerPrefect.append(lastGame)

            for nowGame in nowPrefectGames:
                newFlag = 1
                nowCheckID = nowGame['appid']
                for lastGame in lastPrefectGames:
                    appid = lastGame['appid']
                    if nowCheckID == appid:
                        newFlag = 0
            
                if newFlag:
                    newPrefectGame.append(nowGame)
            logPrint(5,"The new full prefect game and no longer prefect game process completed.")
            emojilist = ['<:catlove:1388792473626607676>','<:meowowo:1388815634779078807>','<:meowwow:1388816426495901766>','<:meowuwu:1388816441502990499>','<:meowok:1388816457718038660>','<:meowdrink:1388816469185527808>']
            #no game change
            if (not noLongerPrefect) and (not newPrefectGame):
                if MessageEveryLoop:
                    nowSelect = random.choice(emojilist)
                    embed=discord.Embed(title=f"{nowSelect}", description="或許你該去買瓶快樂水，然後原神啟動？", color=(0xffb243 if DebugMode else 0x02bc7d))
                    embed.set_author(name="全成就列表已是最新！", icon_url="https://i.imgur.com/QS401hJ.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😎")
                    if DebugMode:
                        embed.add_field(name="**提醒您！**", value="開發者模式已開啟", inline=False)
                    await channel.send(embed=embed)
                
                nowtime = time.localtime()
                formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p",nowtime)
                logPrint(2,f"{formattime} The list of prefect games has not changed.")
                logPrint(5,f"The MessageEveryLoop is set to { "true" if MessageEveryLoop else "false" }\n")
                lastPrefectGames = nowPrefectGames
                try:
                    file_path = os.path.join('db','lastQuery.json')
                    with open(file_path, 'w', encoding='utf-8') as file:
                        json.dump(lastPrefectGames, file, ensure_ascii=False, indent=2)
                    logPrint(2,f"{formattime} The Database has been updated.")
                except Exception as e:
                    embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                    embed.set_author(name="嘗試寫入資料庫時發生錯誤", icon_url="https://i.imgur.com/Z9nqxHg.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                    if DebugMode:
                            embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                    await channel.send(embed=embed)
                    logPrint(4, "Error occurred while attempting to write to database.",e)
            else:
                try:
                    #組合字串
                    noLongerGame = ''
                    for i in noLongerPrefect:
                        noLongerGame += f"[{i['name']}](https://store.steampowered.com/app/{i['appid']})\n"
                    
                    logPrint(5,f"No Longer Game:\n{noLongerGame}------------------------------------------------------------------------------------")

                    newGame = ''
                    for i in newPrefectGame:
                        newGame += f"[{i['name']}](https://store.steampowered.com/app/{i['appid']})\n"

                    logPrint(5,f"New Game:\n{newGame}------------------------------------------------------------------------------------")

                    if len(noLongerGame) == 0:
                        noLongerGame = "無"
                    
                    if len(newGame) == 0:
                        newGame = "無"

                    embed=discord.Embed(title="請查閱以下內容，並更新你的收藏夾 <:meowwow:1388816426495901766>", color=(0xffb243 if DebugMode else 0xe1b243))
                    embed.set_author(name="全成就列表有新的改變！", icon_url="https://i.imgur.com/9TBaz1f.png")
                    embed.add_field(name="以下遊戲已不再是全成就遊戲：", value=f"{noLongerGame}", inline=False)
                    embed.add_field(name="以下遊戲已達成全成就：", value=f"{newGame}", inline=False)
                    if DebugMode:
                        embed.add_field(name="**提醒您！**", value="開發者模式已開啟", inline=False)
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😎")
                    await channel.send(embed=embed)

                    nowtime = time.localtime()
                    formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p",nowtime)
                    logPrint(2,f"{formattime} The list of prefect games has changed!\nGames that are not full achievements:{len(noLongerPrefect)}\nGames that newly achieved full achievements:{len(newPrefectGame)}")
                    logPrint(5,f"No longer prefect games:{noLongerPrefect}\nNewly prefect games:{newPrefectGame}")

                    lastPrefectGames = nowPrefectGames
                    try:
                        file_path = os.path.join('db','lastQuery.json')
                        with open(file_path, 'w', encoding='utf-8') as file:
                            json.dump(lastPrefectGames, file, ensure_ascii=False, indent=2)
                        logPrint(2,f"{formattime} The Database has been updated.")
                    except Exception as e:
                        embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                        embed.set_author(name="嘗試寫入資料庫時發生錯誤", icon_url="https://i.imgur.com/Z9nqxHg.png")
                        embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                        if DebugMode:
                                embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                        await channel.send(embed=embed)
                        logPrint(4, "Error occurred while attempting to write to database.",e)
                except Exception as e:
                    embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                    embed.set_author(name="發送訊息或處理當前列表時發生錯誤", icon_url="https://i.imgur.com/Z9nqxHg.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                    if DebugMode:
                            embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                    await channel.send(embed=embed)
                    logPrint(5,f"Variables\"noLongerPrefect\":{noLongerPrefect}\nVariables\"newPrefectGame\":{newPrefectGame}")
                    logPrint(4,"Error occurred while sending message or processing current list",e)

@tree.command(name="refresh", description="手動重新整理全成就列表")
async def self(interaction: discord.Integration):
    global DebugMode
    global firstUsed
    global lastPrefectGames
    global nowPrefectGames

    await interaction.response.defer()
    
    if firstUsed:
        embed=discord.Embed(title="此指令目前無法使用 <:catqq:1388792459504652298>", description="你必須先進行初始化才能使用此指令。\n嘗試重啟機器人或者確認你的網路連線狀態。", color=0xff5e43)
        embed.set_author(name="禁止的操作", icon_url="https://i.imgur.com/Z9nqxHg.png")
        embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
        await interaction.followup.send(embed=embed)
        logPrint(3,"Cannot used /refresh command without initialization.\nIf you got problem during initialize process, please try to restart your bot or check your internet connection.")
    else:
        if not lastPrefectGames:
            err = f"{lastPrefectGames} list is empty!"

            embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{err}", color=0xff5e43)
            embed.set_author(name="列表為空", icon_url="https://i.imgur.com/Z9nqxHg.png")
            embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
            if DebugMode:
                    embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
            await interaction.followup.send(embed=embed)

            logPrint(4,"Error occurred due to the full achievements list is empty.",err)
        else:
            processEmbed = discord.Embed(
                title="我知道你很急，但是你先別急",
                description="正在調用 Steam API 並更新全成就列表，請稍後...",
                color=0xe1b243
            )
            processEmbed.set_thumbnail(url="https://i.imgur.com/7hlgqYK.png")
            processEmbed.set_author(name="正在處理中......⏳", icon_url="https://i.imgur.com/9TBaz1f.png")
            await interaction.followup.send(embed=processEmbed)

            noLongerPrefect = []
            newPrefectGame = []
            getPrefectGamesList()
            for lastGame in lastPrefectGames:
                prefectFlag = 0
                nowCheckID = lastGame['appid']
                for nowGame in nowPrefectGames:
                    appid = nowGame['appid'] 
                    if nowCheckID == appid:
                        prefectFlag = 1
                
                if not prefectFlag:
                    noLongerPrefect.append(lastGame)

            for nowGame in nowPrefectGames:
                newFlag = 1
                nowCheckID = nowGame['appid']
                for lastGame in lastPrefectGames:
                    appid = lastGame['appid']
                    if nowCheckID == appid:
                        newFlag = 0
            
                if newFlag:
                    newPrefectGame.append(nowGame)
            logPrint(5,"The new full prefect game and no longer prefect game process completed.")
            emojilist = ['<:catlove:1388792473626607676>','<:meowowo:1388815634779078807>','<:meowwow:1388816426495901766>','<:meowuwu:1388816441502990499>','<:meowok:1388816457718038660>','<:meowdrink:1388816469185527808>']
            #no game change
            if (not noLongerPrefect) and (not newPrefectGame):
                if MessageEveryLoop:
                    nowSelect = random.choice(emojilist)
                    embed=discord.Embed(title=f"{nowSelect}", description="或許你該去買瓶快樂水，然後原神啟動？", color=(0xffb243 if DebugMode else 0x02bc7d))
                    embed.set_author(name="全成就列表已是最新！", icon_url="https://i.imgur.com/QS401hJ.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😎")
                    if DebugMode:
                        embed.add_field(name="**提醒您！**", value="開發者模式已開啟", inline=False)
                    await interaction.followup.send(embed=embed)
                
                nowtime = time.localtime()
                formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p",nowtime)
                logPrint(2,f"{formattime} The list of prefect games has not changed.")
                logPrint(5,f"The MessageEveryLoop is set to { "true" if MessageEveryLoop else "false" }\n")
                lastPrefectGames = nowPrefectGames
                try:
                    file_path = os.path.join('db','lastQuery.json')
                    with open(file_path, 'w', encoding='utf-8') as file:
                        json.dump(lastPrefectGames, file, ensure_ascii=False, indent=2)
                    logPrint(2,f"{formattime} The Database has been updated.")
                except Exception as e:
                    embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                    embed.set_author(name="嘗試寫入資料庫時發生錯誤", icon_url="https://i.imgur.com/Z9nqxHg.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                    if DebugMode:
                            embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                    await interaction.followup.send(embed=embed)
                    logPrint(4, "Error occurred while attempting to write to database.",e)
            else:
                try:
                    #組合字串
                    noLongerGame = ''
                    for i in noLongerPrefect:
                        noLongerGame += f"[{i['name']}](https://store.steampowered.com/app/{i['appid']})\n"

                    newGame = ''
                    for i in newPrefectGame:
                        newGame += f"[{i['name']}](https://store.steampowered.com/app/{i['appid']})\n"
                    
                    embed=discord.Embed(title="請查閱以下內容，並更新你的收藏夾 <:meowwow:1388816426495901766>", color=(0xffb243 if DebugMode else 0xe1b243))
                    embed.set_author(name="全成就列表有新的改變！", icon_url="https://i.imgur.com/9TBaz1f.png")
                    embed.add_field(name="以下遊戲已**不再是全成就遊戲**", value=f"{noLongerGame}", inline=False)
                    embed.add_field(name="以下遊戲已**達成全成就**", value=f"{newGame}", inline=False)
                    if DebugMode:
                        embed.add_field(name="**提醒您！**", value="開發者模式已開啟", inline=False)
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😎")
                    await interaction.followup.send(embed=embed)

                    nowtime = time.localtime()
                    formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p",nowtime)
                    logPrint(2,f"{formattime} The list of prefect games has changed!\nGames that are not full achievements:{len(noLongerPrefect)}\nGames that newly achieved full achievements:{len(newPrefectGame)}")
                    logPrint(5,f"No longer prefect games:{noLongerPrefect}\nNewly prefect games:{newPrefectGame}")

                    lastPrefectGames = nowPrefectGames
                    try:
                        file_path = os.path.join('db','lastQuery.json')
                        with open(file_path, 'w', encoding='utf-8') as file:
                            json.dump(lastPrefectGames, file, ensure_ascii=False, indent=2)
                        logPrint(2,f"{formattime} The Database has been updated.")
                    except Exception as e:
                        embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                        embed.set_author(name="嘗試寫入資料庫時發生錯誤", icon_url="https://i.imgur.com/Z9nqxHg.png")
                        embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                        if DebugMode:
                                embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                        await interaction.followup.send(embed=embed)
                        logPrint(4, "Error occurred while attempting to write to database.",e)
                except Exception as e:
                    embed=discord.Embed(title="發生非預期的錯誤，請查看日誌文件。 <:catsad:1388792446229549076> \n錯誤傾印：", description=f"{e}", color=0xff5e43)
                    embed.set_author(name="發送訊息或處理當前列表時發生錯誤", icon_url="https://i.imgur.com/Z9nqxHg.png")
                    embed.set_footer(text=f"Steam 全成就查詢工具版本：{BotVersion} ． Made by whitebear13579 😭")
                    if DebugMode:
                            embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
                    await interaction.followup.send(embed=embed)
                    logPrint(5,f"Variables\"noLongerPrefect\":{noLongerPrefect}\nVariables\"newPrefectGame\":{newPrefectGame}")
                    logPrint(4,"Error occurred while sending message or processing current list",e)

if __name__ == "__main__":
    client.run(BotToken,log_handler=handler)