import discord
from discord import app_commands
from discord.ext import tasks
import time
import os
from modules.logHandler import loggingHandler as log, getLogHandler, getRootLogger
from modules.configHandler import loadConfig
from modules.getPrefectList import getPrefectGamesList
from modules.steamApiHandler import getPlayerProfile
from modules.databaseHandler import loadLastQuery, saveLastQuery, compareGameLists
from modules.discordNotifSender import (
    createStartupEmbed,
    createErrorEmbed,
    createNoChangeEmbed,
    createListChangedEmbed,
    createProcessingEmbed,
    createNotInitializedEmbed
)

config = loadConfig('config.ini', getRootLogger())
if config is None:
    log(4, "Failed to load config, exiting...")
    exit(1)

nowPrefectGames = []
lastPrefectGames = []
firstUsed = True

# discord bot initialization
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    global firstUsed, lastPrefectGames, nowPrefectGames
    
    cmds = await tree.sync()
    log(3, f"Login user : {client.user}")
    log(2, f"{len(cmds)} slash commands loaded.")
    discord.VoiceClient.warn_nacl = False
    
    try:
        lastPrefectGames = loadLastQuery(config.debug_mode)
        
        # db not existed or empty
        if lastPrefectGames is None:
            nowPrefectGames = getPrefectGamesList(config.steam_id, config.steam_api_key, config.debug_mode)
            
            if len(nowPrefectGames) == 0:
                log(3, "The program has TERMINATED due to no data was returned from Steam API.")
                os._exit(1)
            
            log(2, f"Loaded full achievements games: {len(nowPrefectGames)}")
            lastPrefectGames = nowPrefectGames.copy()
            saveLastQuery(lastPrefectGames, config.debug_mode)
            log(3, "\"lastQuery.json\" not existed or empty, automatically created at db folder.")
        else:
            # db existed and has data, send startup message
            channel = await client.fetch_channel(config.broadcast_channel)
            try:
                firstUsed = False
                playerProfile = getPlayerProfile(config.steam_id, config.steam_api_key, config.debug_mode)
                
                if playerProfile is None:
                    raise Exception("Failed to get player profile")
                
                embed = createStartupEmbed(
                    client=client,
                    playerProfile=playerProfile,
                    gamesCount=len(lastPrefectGames),
                    updateFrequency=config.update_frequency,
                    messageEveryLoop=config.message_every_loop,
                    botVersion=config.bot_version,
                    debugMode=config.debug_mode,
                    isFromDatabase=True
                )
                await channel.send(embed=embed)
                log(2, "Successfully loaded last query result in database.")
                
            except Exception as e:
                embed = createErrorEmbed(
                    title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                    errorMessage=str(e),
                    botVersion=config.bot_version,
                    debugMode=config.debug_mode,
                    authorName="工具啟動失敗"
                )
                await channel.send(embed=embed)
                log(4, "Error occurred during initialization.", str(e))
                
    except Exception as e:
        log(4, "Error occurred while loading query data from database\n(may be the json file is broken? try to delete it and the program will automatically create a new one.)", str(e))
    
    if not queryAndBroadcast.is_running():
        queryAndBroadcast.start()
        log(2, f"The task has been started. Automatically refresh frequency is : {config.update_frequency}s")

@tasks.loop(seconds=1)  # default 1s, will be changed in on_ready
async def queryAndBroadcast():
    global firstUsed, lastPrefectGames, nowPrefectGames
    
    channel = await client.fetch_channel(config.broadcast_channel)
    
    if firstUsed:
        try:
            playerProfile = getPlayerProfile(config.steam_id, config.steam_api_key, config.debug_mode)
            
            if playerProfile is None:
                raise Exception("Failed to get player profile")
            
            lastPrefectGames = nowPrefectGames.copy()
            
            embed = createStartupEmbed(
                client=client,
                playerProfile=playerProfile,
                gamesCount=len(lastPrefectGames),
                updateFrequency=config.update_frequency,
                messageEveryLoop=config.message_every_loop,
                botVersion=config.bot_version,
                debugMode=config.debug_mode,
                isFromDatabase=False
            )
            await channel.send(embed=embed)
            
            log(2, "Initialization completed, FIRST USED Mode.")
            firstUsed = False
            
        except Exception as e:
            embed = createErrorEmbed(
                title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                errorMessage=str(e),
                botVersion=config.bot_version,
                debugMode=config.debug_mode,
                authorName="初始化失敗"
            )
            await channel.send(embed=embed)
            log(4, "Error occurred during initialization.", str(e))
    else:
        if not lastPrefectGames:
            err = f"{lastPrefectGames} list is empty!"
            embed = createErrorEmbed(
                title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                errorMessage=err,
                botVersion=config.bot_version,
                debugMode=config.debug_mode,
                authorName="列表為空"
            )
            await channel.send(embed=embed)
            log(4, "Error occurred due to the full achievements list is empty.", err)
        else:
            nowPrefectGames = getPrefectGamesList(config.steam_id, config.steam_api_key, config.debug_mode)
            noLongerPrefect, newPrefectGame = compareGameLists(lastPrefectGames, nowPrefectGames, config.debug_mode)
            
            # if no change
            if (not noLongerPrefect) and (not newPrefectGame):
                if config.message_every_loop:
                    embed = createNoChangeEmbed(config.bot_version, config.debug_mode)
                    await channel.send(embed=embed)
                
                nowtime = time.localtime()
                formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p", nowtime)
                log(2, f"{formattime} The list of prefect games has not changed.")
                log(5, f"The MessageEveryLoop is set to {'true' if config.message_every_loop else 'false'}\n", config.debug_mode)
                
                lastPrefectGames = nowPrefectGames.copy()
                if not saveLastQuery(lastPrefectGames, config.debug_mode):
                    embed = createErrorEmbed(
                        title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                        errorMessage="Database write error",
                        botVersion=config.bot_version,
                        debugMode=config.debug_mode,
                        authorName="嘗試寫入資料庫時發生錯誤"
                    )
                    await channel.send(embed=embed)
            else:
                try:
                    embed = createListChangedEmbed(noLongerPrefect, newPrefectGame, config.bot_version, config.debug_mode)
                    await channel.send(embed=embed)
                    
                    nowtime = time.localtime()
                    formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p", nowtime)
                    log(2, f"{formattime} The list of prefect games has changed!\nGames that are not full achievements:{len(noLongerPrefect)}\nGames that newly achieved full achievements:{len(newPrefectGame)}")
                    log(5, f"No longer prefect games:{noLongerPrefect}\nNewly prefect games:{newPrefectGame}", config.debug_mode)
                    
                    lastPrefectGames = nowPrefectGames.copy()
                    if not saveLastQuery(lastPrefectGames, config.debug_mode):
                        embed = createErrorEmbed(
                            title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                            errorMessage="Database write error",
                            botVersion=config.bot_version,
                            debugMode=config.debug_mode,
                            authorName="嘗試寫入資料庫時發生錯誤"
                        )
                        await channel.send(embed=embed)
                        
                except Exception as e:
                    embed = createErrorEmbed(
                        title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                        errorMessage=str(e),
                        botVersion=config.bot_version,
                        debugMode=config.debug_mode,
                        authorName="發送訊息或處理當前列表時發生錯誤"
                    )
                    await channel.send(embed=embed)
                    log(5, f"Variables\"noLongerPrefect\":{noLongerPrefect}\nVariables\"newPrefectGame\":{newPrefectGame}", config.debug_mode)
                    log(4, "Error occurred while sending message or processing current list", str(e))

@queryAndBroadcast.before_loop
async def before_queryAndBroadcast():
    # wait the bot ready, set the broadcast interval
    await client.wait_until_ready()
    queryAndBroadcast.change_interval(seconds=config.update_frequency)

# /refresh command
@tree.command(name="refresh", description="手動重新整理全成就列表")
async def refresh_command(interaction: discord.Interaction):
    global firstUsed, lastPrefectGames, nowPrefectGames
    
    await interaction.response.defer()
    
    if firstUsed:
        embed = createNotInitializedEmbed(config.bot_version)
        await interaction.followup.send(embed=embed)
        log(3, "Cannot used /refresh command without initialization.\nIf you got problem during initialize process, please try to restart your bot or check your internet connection.")
    else:
        if not lastPrefectGames:
            err = f"{lastPrefectGames} list is empty!"
            embed = createErrorEmbed(
                title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                errorMessage=err,
                botVersion=config.bot_version,
                debugMode=config.debug_mode,
                authorName="列表為空"
            )
            await interaction.followup.send(embed=embed)
            log(4, "Error occurred due to the full achievements list is empty.", err)
        else:
            processEmbed = createProcessingEmbed()
            await interaction.followup.send(embed=processEmbed)

            nowPrefectGames = getPrefectGamesList(config.steam_id, config.steam_api_key, config.debug_mode)
            noLongerPrefect, newPrefectGame = compareGameLists(lastPrefectGames, nowPrefectGames, config.debug_mode)
            
            # if no change
            if (not noLongerPrefect) and (not newPrefectGame):
                if config.message_every_loop:
                    embed = createNoChangeEmbed(config.bot_version, config.debug_mode)
                    await interaction.followup.send(embed=embed)
                
                nowtime = time.localtime()
                formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p", nowtime)
                log(2, f"{formattime} The list of prefect games has not changed.")
                log(5, f"The MessageEveryLoop is set to {'true' if config.message_every_loop else 'false'}\n", config.debug_mode)
                
                lastPrefectGames = nowPrefectGames.copy()
                if not saveLastQuery(lastPrefectGames, config.debug_mode):
                    embed = createErrorEmbed(
                        title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                        errorMessage="Database write error",
                        botVersion=config.bot_version,
                        debugMode=config.debug_mode,
                        authorName="嘗試寫入資料庫時發生錯誤"
                    )
                    await interaction.followup.send(embed=embed)
            else:
                try:
                    embed = createListChangedEmbed(noLongerPrefect, newPrefectGame, config.bot_version, config.debug_mode)
                    await interaction.followup.send(embed=embed)
                    
                    nowtime = time.localtime()
                    formattime = time.strftime("%Y-%m-%d %I：%M：%S：%p", nowtime)
                    log(2, f"{formattime} The list of prefect games has changed!\nGames that are not full achievements:{len(noLongerPrefect)}\nGames that newly achieved full achievements:{len(newPrefectGame)}")
                    log(5, f"No longer prefect games:{noLongerPrefect}\nNewly prefect games:{newPrefectGame}", config.debug_mode)
                    
                    lastPrefectGames = nowPrefectGames.copy()
                    if not saveLastQuery(lastPrefectGames, config.debug_mode):
                        embed = createErrorEmbed(
                            title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                            errorMessage="Database write error",
                            botVersion=config.bot_version,
                            debugMode=config.debug_mode,
                            authorName="嘗試寫入資料庫時發生錯誤"
                        )
                        await interaction.followup.send(embed=embed)
                        
                except Exception as e:
                    embed = createErrorEmbed(
                        title="發生非預期的錯誤，請查看日誌文件。\n錯誤傾印：",
                        errorMessage=str(e),
                        botVersion=config.bot_version,
                        debugMode=config.debug_mode,
                        authorName="發送訊息或處理當前列表時發生錯誤"
                    )
                    await interaction.followup.send(embed=embed)
                    log(5, f"Variables\"noLongerPrefect\":{noLongerPrefect}\nVariables\"newPrefectGame\":{newPrefectGame}", config.debug_mode)
                    log(4, "Error occurred while sending message or processing current list", str(e))

if __name__ == "__main__":
    client.run(config.bot_token, log_handler=getLogHandler())

