from configparser import ConfigParser
from dataclasses import dataclass
from typing import Optional
import logging

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

def loadConfig(configPath: str = 'config.ini', logger: Optional[logging.Logger] = None) -> Optional[Config]:
    
    """
    從設定檔（config.ini）載入設定
    
    Args:
        configPath: path to config.ini
        logger: Logger instance (optional)
    
    Returns:
        Config object, None if loading fails
    """

    conf = ConfigParser()
    try:
        conf.read(configPath, encoding='utf-8')
        
        config = Config(
            steam_api_key = conf['General']['STEAM_API_KEY'],
            steam_id = conf['General']['STEAMID64'],
            broadcast_channel = conf.getint('General', 'BOARDCAST_CHANNEL'),
            bot_token = conf['General']['BOT_TOKEN'],
            update_frequency = conf.getint('General', 'UPDATE_FREQ'),
            message_every_loop = conf.getboolean('General', 'MESSAGE_EVERY_LOOP'),
            bot_version = conf['Debug']['BOT_VERSION'],
            debug_mode = conf.getboolean('Debug', 'DEBUG_MODE')
        )
        
        if logger:
            if config.debug_mode:
                logger.setLevel(logging.DEBUG)
                print("Debug > Debug mode is set to true.")
                logging.debug("Debug > Debug mode is set to true.")
            else:
                logger.setLevel(logging.INFO)
        
        print("Info > Settings has been read from config.ini :D")
        logging.info("Info > Settings has been read from config.ini :D")
        
        return config
        
    except Exception as e:
        print(f"Cannot find \"{configPath}\", please check your bot file is complete !")
        print(e)
        logging.error(f"Cannot find \"{configPath}\", please check your bot file is complete !")
        logging.error(e)
        return None
