# Steam 全成就游戏清单查询器
如果你的 Steam 收藏库中有专门的全成就游戏分类，那么这个机器人可以帮你有效维护你的收藏夹。   
你只需要注册一个 Discord Bot 服务，申请 Steam API Key，这个机器人就会在你设定的时间间隔内定期向 Steam API 获取全成就列表，并通知你哪些游戏已经不再是全成就，或是哪些游戏已达成全成就。   
它也支持斜线命令，你可以使用 "/refresh" 手动更新并检查全成就列表。   

- 初始化完成示例：  
![image](https://i.imgur.com/vfYhIwq.png)   

- 从本地数据库（json）读入并检查到有游戏达成全成就：   
![image](https://i.imgur.com/1ykobMz.png)   

- 使用 /refresh 指令来手动检查列表：   
![image](https://i.imgur.com/5fQT0z4.png)   

## 使用指南
- 将仓库克隆至本地后，请先通过 `requirements.txt` 来安装模块。
    - 使用 pip 来安装
        ```console
        pip install -r requirements.txt
        ```
    - 使用 conda 来安装
        ```console
        conda install --yes --file requirements.txt
        ```

- 接着，请至 `config.ini` 设定以下必要项：
    ```yaml
    - STEAM_API_KEY
    - STEAMID64
    - BOARDCAST_CHANNEL
    - BOT_TOKEN
    ```
    - 如果你不知道某个密钥或 ID 该怎么获取，config 中也有详细的说明。

- 最后，你可以使用此指令来执行程序：
    ```console
    python main.py
    ```
    - 在首次执行时，由于数据库（json）为空，程序会先向 steam API 请求数据并获取全成就游戏清单，这可能会需要一点时间。
    - 往后重新启动时，程序会先从本地 json 中读取数据，再向 steam API 发送请求，启动时间就不会那么久了。
    - 若因非预期原因导致 json 损坏，请放心将整个文件删除（你甚至可以直接删掉 db 文件夹），程序会自动重新初始化。

## 常见问题

### 从数据库读/写时发生问题
```console
Err! > Error occurred while loading query data from database
(may be the json file is broken? try to delete it and the program will automactically create a new one.)
not writable
```
- 解决方案：请先尝试更改 `../db/*` 的权限。 

## 遇到问题了吗？
如果你有任何的意见，或是遇到任何的问题，欢迎你创建一个 issue。   
我也欢迎你使用 Discord 来私信我获取协助：whitebear13579
