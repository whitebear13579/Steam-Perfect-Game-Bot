# Steam パーフェクトゲームリスト検索ツール
もしあなたのSteamライブラリに全実績達成ゲーム専用のカテゴリがあるなら、このボットがコレクションの維持を効果的にサポートします。   
Discord Botサービスの登録とSteam API Keyの申請だけで、このボットが設定した時間間隔でSteam APIから全実績リストを定期的に取得し、どのゲームがもはや全実績ではなくなったか、またはどのゲームが全実績を達成したかを通知します。   
スラッシュコマンドにも対応しており、「/refresh」を使用して手動で全実績リストを更新・確認できます。   

- 初期化完了例：  
![image](https://i.imgur.com/vfYhIwq.png)   

- ローカルデータベース（json）から読み込み、全実績達成ゲームを検出：   
![image](https://i.imgur.com/1ykobMz.png)   

- /refreshコマンドを使用してリストを手動確認：   
![image](https://i.imgur.com/5fQT0z4.png)   

## 使用方法
- リポジトリをローカルにクローンした後、まず`requirements.txt`を通じてモジュールをインストールしてください。
    - pipを使用してインストール
        ```console
        pip install -r requirements.txt
        ```
    - condaを使用してインストール
        ```console
        conda install --yes --file requirements.txt
        ```

- 次に、`config.ini`で以下の必須項目を設定してください：
    ```yaml
    - STEAM_API_KEY
    - STEAMID64
    - BOARDCAST_CHANNEL
    - BOT_TOKEN
    ```
    - キーやIDの取得方法がわからない場合、configファイルに詳細な説明があります。

- 最後に、以下のコマンドでプログラムを実行できます：
    ```console
    python main.py
    ```
    - 初回実行時は、データベース（json）が空のため、プログラムはまずSteam APIにデータを要求し、全実績ゲームリストを取得します。これには少し時間がかかる場合があります。
    - その後の再起動時は、プログラムはまずローカルjsonファイルからデータを読み取り、その後Steam APIにリクエストを送信するため、起動時間は短縮されます。
    - 予期しない理由でjsonファイルが破損した場合は、ファイル全体を削除してください（dbフォルダ全体を削除することも可能）。プログラムが自動的に再初期化します。

## よくある質問

### データベースの読み取り/書き込み時の問題
```console
Err! > Error occurred while loading query data from database
(may be the json file is broken? try to delete it and the program will automactically create a new one.)
not writable
```
- 解決策：まず`../db/*`の権限を変更してみてください。 

## 問題が発生しましたか？
ご意見やご質問がございましたら、issueを作成してください。   
Discordでの直接メッセージによるサポートも歓迎します：whitebear13579
