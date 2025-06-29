# Steam Perfect Games Checking Bot

If you have a dedicated category in your Steam library for games with perfect achievements, this bot can help you maintain your collection effectively.   
You just need to register a Discord Bot service and apply for a Steam API Key. This bot will periodically fetch the perfect achievements list from Steam API at your configured intervals and notify you which games are no longer perfect achievements or which games have achieved perfect achievements.   
It also supports slash commands - you can use "/refresh" to manually update and check the perfect achievements list.   

- Initialization completed example:   
![image](https://i.imgur.com/vfYhIwq.png)   

- Loading from local database (json) and detecting games that achieved perfect achievements:   
![image](https://i.imgur.com/1ykobMz.png)   

- Using /refresh command to manually check the list:   
![image](https://i.imgur.com/5fQT0z4.png)   

## Installation Guide
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