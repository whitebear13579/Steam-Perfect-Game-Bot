# [繁體中文] Steam 全成就遊戲清單查詢器
如果你的 Steam 收藏庫中有專門將全成就的遊戲分類，那麼，這個機器人可以幫你好好維護你的收藏夾。   
你只需要註冊一個 Discord Bot 服務，申請 Steam API Key，這個機器人就會在你設定好的時間裡定時向 Steam API 擷取全成就列表，並通指你哪些遊戲已經不再是全成就，或是哪些遊戲已達成全成就。   
他也支援斜線指令，你可以使用 "/refresh" 手動更新並檢查全成就列表。   

- 初始化完成範例：  
![image](https://i.imgur.com/vfYhIwq.png)   

- 從本地資料庫（json）讀入並檢查到有遊戲達成全成就：   
![image](https://i.imgur.com/1ykobMz.png)   

- 使用 /refresh 指令來手動檢查列表：   
![image](https://i.imgur.com/5fQT0z4.png)   

## 使用指南
- 將倉庫克隆至本地後，請先透過 `requirements.txt` 來安裝模組。
    - 使用 pip 來安裝
        ```console
        pip install -r requirements.txt
        ```
    - 使用 conda 來安裝
        ```console
        conda install --yes --file requirements.txt
        ```

- 接著，請至 `config.ini` 設定以下必要項：
    ```yaml
    - STEAM_API_KEY
    - STEAMID64
    - BOARDCAST_CHANNEL
    - BOT_TOKEN
    ```
    - 如果你不知道某個金鑰或 ID 該怎麼取得，config 中也有詳細的說明。

- 最後，你可以使用此指令來執行程式：
    ```console
    python main.py
    ```
    - 在首次執行時，由於資料庫（json）為空，程式會先向 steam API 資料並取得全成就遊戲清單，這可能會需要一點時間。
    - 往後重新啟動時，程式會先從本地 json 中讀取資料，再向 steam API 發送請求，啟動時間就不會那麼久了。
    - 若因非預期原因導致 json 損毀，請放心將整個檔案刪除（你甚至可以直接刪掉 db 資料夾），程式會自動重新初始化。

## 常見問題

### 從資料庫讀 / 寫時發生問題
```console
Err! > Error occurred while loading query data from database
(may be the json file is broken? try to delete it and the program will automactically create a new one.)
not writable
```
- Solution：請先嘗試變更 `..db/*` 的權限。 

## 遇到問題了嗎？
如果你有任何的意見，或是遇到任何的問題，歡迎你創建一個 issue。   
我也歡迎你使用 Discord 來私訊我取得協助：whitebear13579   

---

# [English] Steam Perfect Games Checking Bot

If you have a dedicated category in your Steam library for games with perfect achievements, this bot can help you maintain your collection effectively.   
You just need to register a Discord Bot service and apply for a Steam API Key. This bot will periodically fetch the perfect achievements list from Steam API at your configured intervals and notify you which games are no longer perfect achievements or which games have achieved perfect achievements.   
It also supports slash commands - you can use "/refresh" to manually update and check the perfect achievements list.   

- Initialization completed example:   
![image](https://i.imgur.com/vfYhIwq.png)   

- Loading from local database (json) and detecting games that achieved perfect achievements:   
![image](https://i.imgur.com/1ykobMz.png)   

- Using /refresh command to manually check the list:   
![image](https://i.imgur.com/5fQT0z4.png)   

## Usage Guide
- After cloning the repository locally, please install the modules via `requirements.txt` first.
    - Install using pip
        ```console
        pip install -r requirements.txt
        ```
    - Install using conda
        ```console
        conda install --yes --file requirements.txt
        ```

- Next, please configure the following required items in `config.ini`:
    ```yaml
    - STEAM_API_KEY
    - STEAMID64
    - BOARDCAST_CHANNEL
    - BOT_TOKEN
    ```
    - If you don't know how to obtain a certain key or ID, there are detailed instructions in the config file.

- Finally, you can use this command to run the program:
    ```console
    python main.py
    ```
    - During the first execution, since the database (json) is empty, the program will first request data from Steam API and obtain the perfect achievements game list, which may take some time.
    - For subsequent restarts, the program will first read data from the local json file, then send requests to Steam API, so the startup time won't be as long.
    - If the json file is corrupted due to unexpected reasons, feel free to delete the entire file (you can even delete the entire db folder), and the program will automatically reinitialize.

## FAQ
### Issues with reading/writing from database
```console
Err! > Error occurred while loading query data from database
(may be the json file is broken? try to delete it and the program will automactically create a new one.)
not writable
```
- Solution: Please try changing the permissions of `../db/*` first.

## Support
If you encounter any issues or have suggestions, please create an issue on GitHub.   
You are also welcome to contact me via Discord for assistance: whitebear13579   