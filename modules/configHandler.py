from dataclasses import dataclass
from typing import Optional
import logging
import json
import os

# default config structure
DEFAULT_CONFIG = {
    "General": {
        "STEAM_API_KEY": "",
        "STEAMID64": "",
        "BOARDCAST_CHANNEL": "",
        "BOT_TOKEN": "",
        "UPDATE_FREQ": 3600,
        "MESSAGE_EVERY_LOOP": True
    },
    "Debug": {
        "DEBUG_MODE": False,
        "BOT_VERSION": "v2.0.0"
    }
}

@dataclass
class Config:
    steam_api_key: str
    steam_id: str
    broadcast_channel: int
    bot_token: str
    update_frequency: int
    message_every_loop: bool
    bot_version: str
    debug_mode: bool


def ensureConfigExists(configPath: str = 'config.json') -> None:

    """
    確保設定檔存在，若不存在則建立預設設定檔
    
    Args:
        configPath: path to config.json
    """

    if not os.path.exists(configPath):
        config_dir = os.path.dirname(configPath)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        with open(configPath, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
        print(f"Info > Config file not found, created default config at {configPath}")
        logging.info(f"Config file not found, created default config at {configPath}")


def loadConfigFromJson(configPath: str = 'config.json') -> dict:

    """
    從 JSON 設定檔載入原始設定資料
    
    Args:
        configPath: path to config.json
    
    Returns:
        dict containing config data
    """

    ensureConfigExists(configPath)
    
    with open(configPath, 'r', encoding='utf-8') as f:
        return json.load(f)


def saveConfigToJson(configData: dict, configPath: str = 'config.json') -> bool:

    """
    將設定資料儲存到 JSON 設定檔
    
    Args:
        configData: config data dictionary
        configPath: path to config.json
    
    Returns:
        bool, whether saving was successful
    """

    try:
        with open(configPath, 'w', encoding='utf-8') as f:
            json.dump(configData, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        logging.error(f"Error saving config: {e}")
        return False


def loadConfig(configPath: str = 'config.json', logger: Optional[logging.Logger] = None) -> Optional[Config]:
    
    """
    從設定檔（config.json）載入設定
    
    Args:
        configPath: path to config.json
        logger: Logger instance (optional)
    
    Returns:
        Config object, None if loading fails
    """

    try:
        ensureConfigExists(configPath)
        
        with open(configPath, 'r', encoding='utf-8') as f:
            conf = json.load(f)
        
        for section, values in DEFAULT_CONFIG.items():
            if section not in conf:
                conf[section] = values
            else:
                for key, default_value in values.items():
                    if key not in conf[section]:
                        conf[section][key] = default_value
        
        broadcast_channel_value = conf['General']['BOARDCAST_CHANNEL']
        if broadcast_channel_value == "" or broadcast_channel_value is None:
            broadcast_channel = 0
        else:
            broadcast_channel = int(broadcast_channel_value)
        
        config = Config(
            steam_api_key = str(conf['General']['STEAM_API_KEY']),
            steam_id = str(conf['General']['STEAMID64']),
            broadcast_channel = broadcast_channel,
            bot_token = str(conf['General']['BOT_TOKEN']),
            update_frequency = int(conf['General']['UPDATE_FREQ']),
            message_every_loop = bool(conf['General']['MESSAGE_EVERY_LOOP']),
            bot_version = str(conf['Debug']['BOT_VERSION']),
            debug_mode = bool(conf['Debug']['DEBUG_MODE'])
        )
        
        if logger:
            if config.debug_mode:
                logger.setLevel(logging.DEBUG)
                print("Debug > Debug mode is set to true.")
                logging.debug("Debug > Debug mode is set to true.")
            else:
                logger.setLevel(logging.INFO)
        
        print("Info > Settings has been read from config.json :D")
        logging.info("Info > Settings has been read from config.json :D")
        
        return config
        
    except Exception as e:
        print(f"Cannot find or parse \"{configPath}\", please check your bot file is complete !")
        print(e)
        logging.error(f"Cannot find or parse \"{configPath}\", please check your bot file is complete !")
        logging.error(e)
        return None
