import discord
from typing import List, Optional
import random

EMOJI_LIST = [
    '<:catlove:1388792473626607676>',
    '<:meowowo:1388815634779078807>',
    '<:meowwow:1388816426495901766>',
    '<:meowuwu:1388816441502990499>',
    '<:meowok:1388816457718038660>',
    '<:meowdrink:1388816469185527808>'
]

def createStartupEmbed(
    client: discord.Client,
    playerProfile: dict,
    gamesCount: int,
    updateFrequency: int,
    messageEveryLoop: bool,
    botVersion: str,
    debugMode: bool,
    isFromDatabase: bool = True
) -> discord.Embed:
    
    """
    建立啟動成功的 Embed 訊息
    
    Args:
        client: discord Client
        playerProfile: player profile
        gamesCount: number of full achievement games
        updateFrequency: update frequency
        messageEveryLoop: whether to send message every loop
        botVersion: bot version
        debugMode: debug mode is opened or not
        isFromDatabase: whether loaded from database
    
    Returns:
        discord.Embed object
    """

    embed = discord.Embed(
        title="已載入設定檔 <:catlove:1388792473626607676>",
        color=(0xffb243 if debugMode else 0x02bc7d)
    )
    embed.set_author(
        name="工具已成功啟動" if isFromDatabase else "工具初始化完成！",
        icon_url="https://i.imgur.com/QS401hJ.png"
    )
    embed.set_thumbnail(url=f"{playerProfile['avatarfull']}")
    embed.add_field(name="登入使用者", value=f"{client.user}", inline=False)
    embed.add_field(
        name="從本地資料庫載入的全成就遊戲列表" if isFromDatabase else "已載入全成就遊戲",
        value=f"{gamesCount}",
        inline=False
    )
    embed.add_field(name="設定查詢頻率（秒）", value=f"{updateFrequency}", inline=False)
    embed.add_field(name="查詢玩家", value=f"{playerProfile['personaname']}", inline=False)
    embed.add_field(name="查詢提示訊息", value=f"{'開啟' if messageEveryLoop else '關閉'}", inline=False)
    
    if isFromDatabase:
        embed.add_field(
            name="請稍後！",
            value="我們正向 Steam API 擷取新列表，若有更新馬上就通知你 <:meowok:1388816457718038660>",
            inline=False
        )
    
    if debugMode:
        embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，這可能導致非預期的錯誤發生。", inline=False)
    
    embed.set_footer(text=f"Steam 全成就查詢工具版本：{botVersion} ． Made by whitebear13579 😎")
    return embed

def createErrorEmbed(
    title: str,
    errorMessage: str,
    botVersion: str,
    debugMode: bool,
    authorName: str = "發生錯誤"
) -> discord.Embed:

    """
    建立錯誤訊息的 Embed 訊息
    
    Args:
        title: title string
        errorMessage: error messages
        botVersion: bot version
        debugMode: debug mode is opened or not
        authorName: author name
    
    Returns:
        discord.Embed object
    """

    embed = discord.Embed(
        title=f"{title} <:catsad:1388792446229549076>",
        description=f"{errorMessage}",
        color=0xff5e43
    )
    embed.set_author(name=authorName, icon_url="https://i.imgur.com/Z9nqxHg.png")
    embed.set_footer(text=f"Steam 全成就查詢工具版本：{botVersion} ． Made by whitebear13579 😭")
    if debugMode:
        embed.add_field(name="**開發者模式已開啟**", value="您已開啟開發者模式，請嘗試關閉後重試。", inline=False)
    return embed

def createNoChangeEmbed(botVersion: str, debugMode: bool) -> discord.Embed:

    """
    建立全成就列表列表無變化的 Embed 訊息
    
    Args:
        botVersion: bot version
        debugMode: debug mode is opened or not
    
    Returns:
        discord.Embed object
    """

    nowSelect = random.choice(EMOJI_LIST)
    embed = discord.Embed(
        title=f"{nowSelect}",
        description="或許你該去買瓶快樂水，然後原神啟動？",
        color=(0xffb243 if debugMode else 0x02bc7d)
    )
    embed.set_author(name="全成就列表已是最新！", icon_url="https://i.imgur.com/QS401hJ.png")
    embed.set_footer(text=f"Steam 全成就查詢工具版本：{botVersion} ． Made by whitebear13579 😎")
    if debugMode:
        embed.add_field(name="**提醒您！**", value="開發者模式已開啟", inline=False)
    return embed

def createListChangedEmbed(
    noLongerPrefect: List[dict],
    newPrefectGame: List[dict],
    botVersion: str,
    debugMode: bool
) -> discord.Embed:
    
    """
    建立全成就列表有變化的 Embed
    
    Args:
        noLongerPrefect: no longer full achievement game list
        newPrefectGame: new full achievement game list
        botVersion: bot version
        debugMode: debug mode is opened or not
    
    Returns:
        discord.Embed object
    """
    
    noLongerGame = ''
    for i in noLongerPrefect:
        noLongerGame += f"[{i['name']}](https://store.steampowered.com/app/{i['appid']})\n"
    
    newGame = ''
    for i in newPrefectGame:
        newGame += f"[{i['name']}](https://store.steampowered.com/app/{i['appid']})\n"
    
    if len(noLongerGame) == 0:
        noLongerGame = "無"
    
    if len(newGame) == 0:
        newGame = "無"
    
    embed = discord.Embed(
        title="請查閱以下內容，並更新你的收藏夾 <:meowwow:1388816426495901766>",
        color=(0xffb243 if debugMode else 0xe1b243)
    )
    embed.set_author(name="全成就列表有新的改變！", icon_url="https://i.imgur.com/9TBaz1f.png")
    embed.add_field(name="以下遊戲已不再是全成就遊戲：", value=f"{noLongerGame}", inline=False)
    embed.add_field(name="以下遊戲已達成全成就：", value=f"{newGame}", inline=False)
    if debugMode:
        embed.add_field(name="**提醒您！**", value="開發者模式已開啟", inline=False)
    embed.set_footer(text=f"Steam 全成就查詢工具版本：{botVersion} ． Made by whitebear13579 😎")
    return embed

def createProcessingEmbed() -> discord.Embed:

    """
    處理中 Embed 訊息 (/refresh)
    
    Returns:
        discord.Embed object
    """

    embed = discord.Embed(
        title="我知道你很急，但是你先別急",
        description="正在調用 Steam API 並更新全成就列表，請稍後...",
        color=0xe1b243
    )
    embed.set_thumbnail(url="https://i.imgur.com/7hlgqYK.png")
    embed.set_author(name="正在處理中......⏳", icon_url="https://i.imgur.com/9TBaz1f.png")
    return embed

def createNotInitializedEmbed(botVersion: str) -> discord.Embed:

    """
    尚未初始化的 Embed 訊息 (/refresh)
    
    Args:
        botVersion: bot version
    
    Returns:
        discord.Embed object
    """
    
    embed = discord.Embed(
        title="此指令目前無法使用 <:catqq:1388792459504652298>",
        description="你必須先進行初始化才能使用此指令。\n嘗試重啟機器人或者確認你的網路連線狀態。",
        color=0xff5e43
    )
    embed.set_author(name="禁止的操作", icon_url="https://i.imgur.com/Z9nqxHg.png")
    embed.set_footer(text=f"Steam 全成就查詢工具版本：{botVersion} ． Made by whitebear13579 😭")
    return embed
