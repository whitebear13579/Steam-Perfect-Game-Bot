import flet as ft
import configparser
import subprocess
import sys
import os

# 全域：用來記錄 Bot 子程序
bot_process = None

def main(page: ft.Page):
    page.title = "Steam 全成就機器人控制台"
    
    # 1. 修改為深色模式
    page.theme_mode = ft.ThemeMode.DARK 
    
    page.window_width = 500
    page.window_height = 800
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 10 

    # ======================================================
    # 全域 Snackbar (設定 duration=1500，即 1.5 秒後自動消失)
    # ======================================================
    snackbar = ft.SnackBar(ft.Text(""), open=False, duration=1000)
    page.overlay.append(snackbar)

    def show_message(msg: str):
        snackbar.content = ft.Text(msg)
        snackbar.open = True
        page.update()

    # ======================================================
    # Config 初始化與讀寫
    # ======================================================
    config = configparser.ConfigParser()
    config_file = "config.ini"

    DEFAULT_CONFIG = {
        "General": {
            "STEAM_API_KEY": "",
            "STEAMID64": "",
            "BOARDCAST_CHANNEL": "",
            "BOT_TOKEN": "",
            "UPDATE_FREQ": "3600",
            "MESSAGE_EVERY_LOOP": "true",
        },
        "Debug": {
            "DEBUG_MODE": "false",
        },
    }

    def ensure_config_exists():
        if not os.path.exists(config_file):
            for section, values in DEFAULT_CONFIG.items():
                config[section] = values
            with open(config_file, "w", encoding="utf-8") as f:
                config.write(f)

    def load_config():
        ensure_config_exists()
        config.read(config_file, encoding="utf-8")

        for section, values in DEFAULT_CONFIG.items():
            if section not in config:
                config[section] = values

        steam_api.value = config["General"].get("STEAM_API_KEY", "")
        steam_id.value = config["General"].get("STEAMID64", "")
        discord_channel.value = config["General"].get("BOARDCAST_CHANNEL", "")
        bot_token.value = config["General"].get("BOT_TOKEN", "")
        update_freq.value = config["General"].get("UPDATE_FREQ", "3600")
        msg_every_loop.value = config["General"].getboolean("MESSAGE_EVERY_LOOP", fallback=True)
        debug_mode.value = config["Debug"].getboolean("DEBUG_MODE", fallback=False)
        page.update()

    def save_config(e):
        try:
            if "General" not in config: config["General"] = {}
            if "Debug" not in config: config["Debug"] = {}

            config["General"]["STEAM_API_KEY"] = steam_api.value
            config["General"]["STEAMID64"] = steam_id.value
            config["General"]["BOARDCAST_CHANNEL"] = discord_channel.value
            config["General"]["BOT_TOKEN"] = bot_token.value
            config["General"]["UPDATE_FREQ"] = update_freq.value
            config["General"]["MESSAGE_EVERY_LOOP"] = str(msg_every_loop.value).lower()
            config["Debug"]["DEBUG_MODE"] = str(debug_mode.value).lower()

            with open(config_file, "w", encoding="utf-8") as f:
                config.write(f)

            show_message("設定已儲存！請重新啟動 Bot 以套用新設定。")
        except Exception as ex:
            show_message(f"儲存失敗: {ex}")

    # ======================================================
    # Bot 啟停邏輯
    # ======================================================
    def stop_bot():
        global bot_process
        if bot_process is None: return
        try:
            bot_process.terminate()
            try:
                bot_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                bot_process.kill()
        except Exception:
            pass
        bot_process = None

    def toggle_bot(e):
        global bot_process
        if bot_process is not None:
            stop_bot()
            status_text.value = "狀態：已停止 🔴"
            status_text.color = ft.Colors.RED_400
            btn_start_stop.text = "啟動機器人"
            btn_start_stop.icon = ft.Icons.PLAY_ARROW
            btn_start_stop.bgcolor = ft.Colors.GREEN_700 
            page.update()
            show_message("Bot 已停止。")
            return

        if not os.path.exists("main.py"):
            show_message("找不到 main.py，無法啟動 Bot。")
            return

        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            bot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=os.getcwd(),
                creationflags=creation_flags,
            )

            status_text.value = "狀態：執行中 🟢"
            status_text.color = ft.Colors.GREEN_400
            btn_start_stop.text = "停止機器人"
            btn_start_stop.icon = ft.Icons.STOP
            btn_start_stop.bgcolor = ft.Colors.RED_700
            page.update()
            show_message("Bot 已啟動！")
        except Exception as ex:
            show_message(f"啟動失敗: {ex}")

    # ======================================================
    # UI 控制項定義
    # ======================================================

    steam_api = ft.TextField(
        label="Steam API Key", 
        password=True, 
        can_reveal_password=True, 
        prefix_icon=ft.Icons.KEY
    )
    
    steam_id = ft.TextField(
        label="Steam ID 64", 
        prefix_icon=ft.Icons.PERSON
    )
    
    bot_token = ft.TextField(
        label="Discord Bot Token", 
        password=True, 
        can_reveal_password=True, 
        prefix_icon=ft.Icons.TOKEN
    )
    
    discord_channel = ft.TextField(
        label="Channel ID", 
        prefix_icon=ft.Icons.ANNOUNCEMENT
    )
    
    update_freq = ft.TextField(
        label="更新頻率 (秒)", 
        prefix_icon=ft.Icons.TIMER, 
        suffix_text="秒"
    )

    msg_every_loop = ft.Switch(label="每次循環都發送訊息", value=True)
    debug_mode = ft.Switch(label="Debug 模式 (詳細日誌)", value=False)

    # 首頁元件
    status_text = ft.Text("狀態：未啟動 ⚪", size=20, weight=ft.FontWeight.BOLD)
    btn_start_stop = ft.ElevatedButton(
        text="啟動機器人",
        icon=ft.Icons.PLAY_ARROW,
        on_click=toggle_bot,
        height=50,
        width=200,
        bgcolor=ft.Colors.GREEN_700, 
        color=ft.Colors.WHITE
    )

    # ======================================================
    # 2. 輔助函式：建立帶有「可點擊連結」或「說明」的輸入框
    # ======================================================
    
    def create_field_with_hint(field, hint_text, url=None):
        """
        建立一個包含輸入框和提示的組合。
        如果提供了 url，提示文字會變成藍色可點擊的連結。
        """
        if url:
            # 如果是網址，做成可點擊的連結 (藍色 + 外連圖示)
            hint_content = ft.Row(
                [
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=14, color=ft.Colors.BLUE_400),
                    ft.Text(
                        spans=[
                            ft.TextSpan(
                                hint_text, 
                                url=url, 
                                style=ft.TextStyle(color=ft.Colors.BLUE_400, weight=ft.FontWeight.BOLD)
                            )
                        ],
                        size=12,
                    )
                ],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        else:
            # 如果只是普通說明文字
            hint_content = ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=14, color=ft.Colors.GREY_500),
                    ft.Text(hint_text, size=12, color=ft.Colors.GREY_500)
                ],
                spacing=5,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

        return ft.Column([
            field,
            hint_content
        ], spacing=3) 

    def create_settings_card(title: str, controls: list):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_200),
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Column(controls, spacing=20)
            ]),
            padding=20,
            bgcolor=ft.Colors.GREY_900, 
            border_radius=12, 
        )

    # ======================================================
    # 頁面佈局
    # ======================================================

    # 第 1 頁：控制台
    page_1 = ft.Container(
        content=ft.Column(
            [
                ft.Image(src="https://i.imgur.com/QS401hJ.png", width=150, height=150),
                ft.Text("Steam Perfect Game Bot", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(color=ft.Colors.GREY_800),
                status_text,
                ft.Container(height=20),
                btn_start_stop,
                ft.Container(height=20),
                ft.Text("點擊按鈕來啟動或停止背景的 Python Bot 程式。", color=ft.Colors.GREY_500),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True
    )

    # 第 2 頁：設定
    page_2 = ft.ListView(
        [
            ft.Text("設定參數", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("修改後請重啟 Bot 生效", size=12, color=ft.Colors.GREY),
            ft.Container(height=10),
            
            # 卡片 1: API 與 驗證
            create_settings_card("🔑  API 與 驗證", [
                create_field_with_hint(steam_api, "前往申請 Steam API Key", url="https://steamcommunity.com/dev/apikey"),
                create_field_with_hint(steam_id, "前往查詢 Steam ID 64", url="https://steamid.io/"),
                create_field_with_hint(bot_token, "前往 Discord 開發者門戶", url="https://discord.com/developers/applications")
            ]),
            ft.Container(height=10),

            # 卡片 2: 機器人行為
            create_settings_card("🤖  Bot Setting", [
                create_field_with_hint(discord_channel, "說明：開啟 Discord 開發者模式 -> 右鍵點擊頻道 -> 複製 ID"),
                create_field_with_hint(update_freq, "說明：預設建議為 3600 秒 (一小時)")
            ]),
            ft.Container(height=10),

            # 卡片 3: 進階選項
            create_settings_card("⚙️  進階選項", [msg_every_loop, debug_mode]),
            ft.Container(height=20),

            ft.ElevatedButton(
                "儲存設定",
                icon=ft.Icons.SAVE,
                on_click=save_config,
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                height=50,
            ),
            ft.Container(height=50),
        ],
        expand=True,
        padding=20, 
        spacing=10,
    )

    # 第 3 頁：關於
    page_3 = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.INFO, size=60, color=ft.Colors.CYAN),
                ft.Text("關於本程式", size=30, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Text("Made by whitebear13579", size=16),
                ft.Text("GUI Optimized with Flet", size=14, color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Text("版本: v1.0", color=ft.Colors.BLACK),
                    bgcolor=ft.Colors.CYAN_200,
                    padding=10,
                    border_radius=5
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True
    )

    pages_list = [page_1, page_2, page_3]

    content_area = ft.Container(expand=True)
    content_area.content = page_1

    def tab_change(e):
        index = e.control.selected_index
        content_area.content = pages_list[index]
        if index == 1:
            load_config()
        page.update()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="控制台"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="設定"),
            ft.NavigationBarDestination(icon=ft.Icons.INFO, label="關於"),
        ],
        selected_index=0,
        on_change=tab_change,
        bgcolor=ft.Colors.GREY_900,
        indicator_color=ft.Colors.BLUE_GREY_700
    )

    load_config()
    page.add(content_area)

    def on_window_event(e):
        if e.data == "close":
            stop_bot()
            page.window_destroy()

    page.on_window_event = on_window_event
    page.window_prevent_close = True

ft.app(target=main)