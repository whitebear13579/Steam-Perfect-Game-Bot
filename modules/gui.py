import flet as ft
import subprocess
import sys
import os
import threading
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.configHandler import loadConfigFromJson, saveConfigToJson, DEFAULT_CONFIG

bot_process = None

def run_bot_process(config_path, log_path, db_path, resource_path):
    os.environ["STEAM_BOT_CONFIG_PATH"] = config_path
    os.environ["STEAM_BOT_LOG_PATH"] = log_path
    os.environ["STEAM_BOT_DB_PATH"] = db_path
    
    if resource_path not in sys.path:
        sys.path.insert(0, resource_path)
    
    from modules.bot import run_bot
    run_bot()

def main(page: ft.Page):
    page.title = "Steam 全成就查詢工具"
    page.theme_mode = ft.ThemeMode.DARK 
    
    page.window.width = 650
    page.window.height = 800
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 10 

    def get_resource_path(relative_path):
        try:
            # pyInstaller pack to exe
            base_path = sys._MEIPASS
        except AttributeError:
            # dev env
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
    def get_data_path(relative_path):
        try:
            # pyInstaller pack to exe
            base_path = sys._MEIPASS
            # automatically use documents folder for user data
            app_data_dir = os.path.join(os.path.expanduser("~"), "Documents", "Steam全成就查詢工具")
            os.makedirs(app_data_dir, exist_ok=True)
            return os.path.join(app_data_dir, relative_path)
        except AttributeError:
            # dev env
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)
    
    project_root = get_data_path("")
    config_file = get_data_path(os.path.join("db", "config.json"))
    bot_py_path = get_resource_path(os.path.join("modules", "bot.py"))

    snackbar = ft.SnackBar(ft.Text(""), open=False, duration=1000)
    page.overlay.append(snackbar)

    def show_message(msg: str):
        snackbar.content = ft.Text(msg)
        snackbar.open = True
        page.update()

    def ensure_config_exists():
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        if not os.path.exists(config_file):
            saveConfigToJson(DEFAULT_CONFIG, config_file)

    def load_config():
        ensure_config_exists()
        try:
            config = loadConfigFromJson(config_file)
            
            steam_api.value = str(config["General"].get("STEAM_API_KEY", ""))
            steam_id.value = str(config["General"].get("STEAMID64", ""))
            discord_channel.value = str(config["General"].get("BOARDCAST_CHANNEL", ""))
            bot_token.value = str(config["General"].get("BOT_TOKEN", ""))
            update_freq.value = str(config["General"].get("UPDATE_FREQ", 3600))
            msg_every_loop_switch.value = config["General"].get("MESSAGE_EVERY_LOOP", True)
            debug_mode_switch.value = config["Debug"].get("DEBUG_MODE", False)
            page.update()
        except Exception as e:
            show_message(f"設定檔載入失敗: {e}")

    def save_config(e):
        try:
            config = {
                "General": {
                    "STEAM_API_KEY": steam_api.value or "",
                    "STEAMID64": steam_id.value or "",
                    "BOARDCAST_CHANNEL": discord_channel.value or "",
                    "BOT_TOKEN": bot_token.value or "",
                    "UPDATE_FREQ": int(update_freq.value) if update_freq.value else 3600,
                    "MESSAGE_EVERY_LOOP": msg_every_loop_switch.value
                },
                "Debug": {
                    "DEBUG_MODE": debug_mode_switch.value,
                    "BOT_VERSION": DEFAULT_CONFIG["Debug"]["BOT_VERSION"]
                }
            }
            
            if saveConfigToJson(config, config_file):
                show_message("設定已儲存！重啟 Bot 來套用新設定。")
            else:
                show_message("儲存失敗！")
        except ValueError as ve:
            show_message(f"請輸入有效的數字作為更新頻率: {ve}")
        except Exception as ex:
            show_message(f"儲存失敗: {ex}")

    def stop_bot():
        global bot_process
        if bot_process is None: 
            return
        try:
            bot_process.terminate()
            bot_process.join(timeout=3)
            if bot_process.is_alive():
                bot_process.kill()
        except Exception:
            pass
        bot_process = None
        
        # clear status file
        status_file = os.path.join(project_root, "db", "bot_status.lock")
        if os.path.exists(status_file):
            try:
                os.remove(status_file)
            except Exception:
                pass

    def toggle_bot(e):
        global bot_process
        if bot_process is not None:
            stop_bot()
            status_icon.content = ft.Text("💤", size=100)
            status_text.value = "狀態：已停止 🔴"
            status_text.color = ft.Colors.RED_400
            btn_start_stop.text = "啟動機器人"
            btn_start_stop.icon = ft.Icons.PLAY_ARROW
            btn_start_stop.bgcolor = ft.Colors.GREEN_700 
            page.update()
            show_message("Bot 已停止。")
            return

        try:
            config = loadConfigFromJson(config_file)
            missing_fields = []
            
            if not config["General"].get("STEAM_API_KEY"):
                missing_fields.append("Steam API Key")
            if not config["General"].get("STEAMID64"):
                missing_fields.append("Steam ID 64")
            if not config["General"].get("BOARDCAST_CHANNEL"):
                missing_fields.append("Channel ID")
            if not config["General"].get("BOT_TOKEN"):
                missing_fields.append("Discord Bot Token")
            
            if missing_fields:
                show_message(f"請先填寫必要設定：{', '.join(missing_fields)}")
                return
        except Exception as ex:
            show_message(f"讀取設定失敗: {ex}")
            return

        # status file route
        status_file = os.path.join(project_root, "db", "bot_status.lock")
        
        try:
            btn_start_stop.disabled = True
            btn_start_stop.bgcolor = ft.Colors.GREY
            page.update()
            
            os.makedirs(os.path.join(project_root, "db"), exist_ok=True)
            os.makedirs(get_data_path("log"), exist_ok=True)
            
            if os.path.exists(status_file):
                os.remove(status_file)

            status_icon.content = ft.ProgressRing(width=100, height=100, stroke_width=8, color=ft.Colors.CYAN_400)
            status_text.value = "狀態：啟動中... ⏳"
            status_text.color = ft.Colors.YELLOW_400
            page.update()

            bot_process = multiprocessing.Process(
                target=run_bot_process,
                args=(config_file, get_data_path("log"), get_data_path("db"), get_resource_path("")),
                daemon=True
            )
            bot_process.start()

            def check_bot_startup():
                global bot_process
                import time
                
                # wait up to 30 seconds for bot to create status file
                for _ in range(60):
                    time.sleep(0.5)
                    
                    if bot_process is None:
                        return  # manually stopped
                    
                    # startup failed
                    if not bot_process.is_alive():
                        error_icon_path = get_resource_path(os.path.join("icon", "error.png"))
                        status_icon.content = ft.Image(src=error_icon_path, width=150, height=150, fit=ft.ImageFit.CONTAIN)
                        status_text.value = f"狀態：啟動失敗 🔴 (退出碼: {bot_process.exitcode})"
                        status_text.color = ft.Colors.RED_400
                        btn_start_stop.text = "啟動機器人"
                        btn_start_stop.icon = ft.Icons.PLAY_ARROW
                        btn_start_stop.bgcolor = ft.Colors.GREEN_700
                        btn_start_stop.disabled = False
                        bot_process = None
                        page.update()
                        return
                    
                    # startup succeeded
                    if os.path.exists(status_file):
                        ok_icon_path = get_resource_path(os.path.join("icon", "ok.png"))
                        status_icon.content = ft.Image(src=ok_icon_path, width=150, height=150, fit=ft.ImageFit.CONTAIN)
                        status_text.value = "狀態：執行中 🟢"
                        status_text.color = ft.Colors.GREEN_400
                        btn_start_stop.text = "停止機器人"
                        btn_start_stop.icon = ft.Icons.STOP
                        btn_start_stop.bgcolor = ft.Colors.RED_700
                        btn_start_stop.disabled = False
                        page.update()
                        show_message("Bot 已成功連線至 Discord！")
                        return
                
                # TLE, same as startup failed
                if bot_process is not None:
                    error_icon_path = get_resource_path(os.path.join("icon", "error.png"))
                    status_icon.content = ft.Image(src=error_icon_path, width=150, height=150, fit=ft.ImageFit.CONTAIN)
                    status_text.value = "狀態：啟動超時 🔴"
                    status_text.color = ft.Colors.RED_400
                    btn_start_stop.text = "停止機器人"
                    btn_start_stop.icon = ft.Icons.STOP
                    btn_start_stop.bgcolor = ft.Colors.RED_700
                    btn_start_stop.disabled = False
                    page.update()
                    show_message("Bot 啟動超時，請檢查設定或網路連線。")

            threading.Thread(target=check_bot_startup, daemon=True).start()

        except Exception as ex:
            error_icon_path = get_resource_path(os.path.join("icon", "error.png"))
            status_icon.content = ft.Image(src=error_icon_path, width=150, height=150, fit=ft.ImageFit.CONTAIN)
            status_text.value = "狀態：啟動失敗 🔴"
            status_text.color = ft.Colors.RED_400
            btn_start_stop.disabled = False
            bot_process = None
            page.update()
            show_message(f"啟動失敗: {ex}")

    """
    
    ui components

    """

    steam_api = ft.TextField(
        label="Steam API Key", 
        password=True, 
        can_reveal_password=True, 
        prefix_icon=ft.Icons.KEY,
        border_color=ft.Colors.GREY_700,
        focused_border_color=ft.Colors.GREY_500
    )
    
    steam_id = ft.TextField(
        label="Steam ID 64", 
        prefix_icon=ft.Icons.PERSON,
        border_color=ft.Colors.GREY_700,
        focused_border_color=ft.Colors.GREY_500
    )
    
    bot_token = ft.TextField(
        label="Discord Bot Token", 
        password=True, 
        can_reveal_password=True, 
        prefix_icon=ft.Icons.TOKEN,
        border_color=ft.Colors.GREY_700,
        focused_border_color=ft.Colors.GREY_500
    )
    
    discord_channel = ft.TextField(
        label="Channel ID", 
        prefix_icon=ft.Icons.ANNOUNCEMENT,
        border_color=ft.Colors.GREY_700,
        focused_border_color=ft.Colors.GREY_500
    )
    
    update_freq = ft.TextField(
        label="更新頻率 (秒)", 
        prefix_icon=ft.Icons.TIMER, 
        suffix_text="秒",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=ft.Colors.GREY_700,
        focused_border_color=ft.Colors.GREY_500
    )

    msg_every_loop_switch = ft.Switch(value=True)
    msg_every_loop = ft.Row(
        [
            ft.Text("每次循環都發送訊息", size=16),
            msg_every_loop_switch
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )
    
    debug_mode_switch = ft.Switch(value=False)
    debug_mode = ft.Row(
        [
            ft.Text("開發者模式", size=16),
            debug_mode_switch
        ],
        spacing=20,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    status_icon_content = ft.Text("💤", size=100)
    status_icon = ft.Container(
        content=status_icon_content,
        alignment=ft.alignment.center,
        width=150,
        height=150
    )
    status_text = ft.Text("狀態：未啟動 ⚪", size=20, weight=ft.FontWeight.BOLD)
    btn_start_stop = ft.ElevatedButton(
        text="啟動機器人",
        icon=ft.Icons.PLAY_ARROW,
        on_click=toggle_bot,
        height=50,
        width=200,
        bgcolor=ft.Colors.GREEN_700, 
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
            icon_size=24
        ),
        
    )
    
    def create_field_with_hint(field, hint_text, url=None):
        if url:
            hint_content = ft.Row(
                [
                    ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=ft.Colors.BLUE_400),
                    ft.Text(
                        spans=[
                            ft.TextSpan(
                                hint_text, 
                                url=url, 
                                style=ft.TextStyle(color=ft.Colors.BLUE_400, weight=ft.FontWeight.BOLD)
                            )
                        ],
                        size=16,
                    )
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )
        else:
            hint_content = ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color=ft.Colors.GREY_500),
                    ft.Text(hint_text, size=16, color=ft.Colors.GREY_500)
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

        return ft.Column([
            field,
            hint_content
        ], spacing=3) 

    def create_settings_card(title: str, controls: list):
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_500),
                ft.Divider(height=5, color=ft.Colors.TRANSPARENT),
                ft.Column(controls, spacing=20)
            ]),
            padding=25,
            bgcolor=ft.Colors.GREY_900, 
            border_radius=12, 
        )

    """

    pages layout
    
    """

    # startup pages
    page_1 = ft.Container(
        content=ft.Column(
            [
                status_icon,
                ft.Text("Steam 全成就查詢機器人", size=36, weight=ft.FontWeight.BOLD),
                ft.Divider(color=ft.Colors.GREY_800),
                status_text,
                ft.Container(height=20),
                btn_start_stop,
                ft.Container(height=20),
                ft.Text("點擊按鈕來啟動或停止 Python Bot", color=ft.Colors.GREY_500, size=18),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True
    )

    # settings pages
    page_2 = ft.ListView(
        [
            ft.Text("設定參數", size=32, weight=ft.FontWeight.BOLD),
            ft.Text("參數修改後需要重啟機器人才會套用設定", size=18, color=ft.Colors.GREY),
            ft.Container(height=10),
            
            create_settings_card("金鑰與令牌設定", [
                create_field_with_hint(steam_api, "前往申請 Steam API Key", url="https://steamcommunity.com/dev/apikey"),
                create_field_with_hint(steam_id, "前往查詢 Steam ID 64", url="https://steamid.io/"),
                create_field_with_hint(bot_token, "前往 Discord Developers 註冊一個 Applications", url="https://discord.com/developers/applications")
            ]),
            ft.Container(height=10),

            create_settings_card("Discord Bot 行為設定", [
                create_field_with_hint(discord_channel, "提示：開啟 Discord 開發者模式 -> 右鍵點擊頻道 -> 複製 ID"),
                create_field_with_hint(update_freq, "提示：以秒為單位，預設為 3600 秒 (一小時)")
            ]),
            ft.Container(height=10),

            create_settings_card("進階選項", [msg_every_loop, debug_mode]),
            ft.Container(height=20),

            ft.ElevatedButton(
                "儲存設定",
                icon=ft.Icons.SAVE,
                on_click=save_config,
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                height=50,
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
                    icon_size=24
                ),
            ),
            ft.Container(height=50),
        ],
        expand=True,
        padding=20, 
        spacing=10,
    )

    # about pages
    page_3 = ft.Container(
        content=ft.Column(
            [
                ft.Image(src=get_resource_path(os.path.join("icon", "bot.png")), width=150, height=150),
                ft.Text("關於 Steam 全成就查詢工具", size=45, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                ft.Text("Made by whitebear13579", size=20),
                ft.Text(
                    spans=[
                        ft.TextSpan("Contribute with "),
                        ft.TextSpan("@Harry55", url="https://github.com/Harry55", style=ft.TextStyle(color=ft.Colors.BLUE_400)),
                        ft.TextSpan(", "),
                        ft.TextSpan("@MiyaOuO2003", url="https://github.com/MiyaOuO2003", style=ft.TextStyle(color=ft.Colors.BLUE_400)),
                        ft.TextSpan(" and "),
                        ft.TextSpan("@yue-meow", url="https://github.com/yue-meow", style=ft.TextStyle(color=ft.Colors.BLUE_400)),
                        ft.TextSpan("."),
                    ],
                    size=16
                ),
                ft.Text("由 Flet GUI 強力驅動 ⚡ 基於 GPL-3.0 License", size=14, color=ft.Colors.GREY_400),
                ft.Container(height=10),
                ft.ElevatedButton(
                    "造訪 GitHub 頁面",
                    icon=ft.Icons.CODE,
                    url="https://github.com/whitebear13579/Steam-Perfect-Game-Bot",
                    bgcolor=ft.Colors.CYAN_200,
                    color=ft.Colors.BLACK,
                    height=50,
                    style=ft.ButtonStyle(
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
                        icon_size=24
                    ),
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.INFO, color=ft.Colors.BLACK, size=24),
                            ft.Text(f"版本: {DEFAULT_CONFIG['Debug']['BOT_VERSION']}", color=ft.Colors.BLACK, size=18, weight=ft.FontWeight.BOLD),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                    bgcolor=ft.Colors.CYAN_200,
                    padding=ft.padding.symmetric(horizontal=20, vertical=12),
                    border_radius=50,
                    height=50,
                    width=180
                ),
                ft.Container(height=20),
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
            page.window.destroy()

    page.window.on_event = on_window_event
    page.window.prevent_close = True

if __name__ == "__main__":
    ft.app(target=main)
