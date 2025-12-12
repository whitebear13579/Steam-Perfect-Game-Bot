import logging
from typing import Optional
import time
import os

# logger settings
istime = time.localtime()
isname = time.strftime("%Y-%m-%d %I：%M：%S：%p", istime)

log_base_path = os.environ.get('STEAM_BOT_LOG_PATH', './log')
os.makedirs(log_base_path, exist_ok=True)

rootLogger = logging.getLogger()
handler = logging.FileHandler(os.path.join(log_base_path, f'Log-{isname}.log'), 'w', 'utf-8')
rootLogger.addHandler(handler)

def loggingHandler(level: int, message: str, debuggingMode: Optional[bool] = False, errCode: Optional[str] = None):

    """
    日誌紀錄處理函式

    Args:
        level: logs level (1=Term, 2=Info, 3=Warn, 4=Error, 5=Debug)
        message: logs message
        debuggingMode: whether debug mode is enabled (only effective for level 5) (optional)
        errCode: error code or detailed error message (optional)
    """

    if level == 1:
        print(f"Term > {message}")
    elif level == 2:
        print(f"Info > {message}")
        logging.info(f"Info > {message}")
    elif level == 3:
        print(f"Warn > {message}")
        logging.warning(f"Warn > {message}")
    elif level == 4:
        print(f"Err! > {message}")
        if errCode:
            print(errCode)
        logging.error(f"Err! > {message}")
        if errCode:
            logging.error(errCode)
    elif level == 5 and debuggingMode:
        print(f"Debug > {message}")
        logging.debug(f"Debug > {message}")

def getLogHandler():
    return handler

def getRootLogger():
    return rootLogger

def initFolders():
    db_base_path = os.environ.get('STEAM_BOT_DB_PATH', './db')
    
    if not os.path.exists(log_base_path):
        os.makedirs(log_base_path)
        loggingHandler(2, "Log folder not existed, create a new one.")

    if not os.path.exists(db_base_path):
        os.makedirs(db_base_path)
        loggingHandler(2, "DB folder not existed, create a new one.")

    loggingHandler(2, "Folder integrity check completed.")

initFolders()