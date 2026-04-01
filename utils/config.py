import configparser
import os
import time

path = 'utils/config.ini'


def create_config():
    config = configparser.ConfigParser()
    config.add_section("Settings")
    config.set("Settings", "bot_token", "token")
    config.set("Settings", "admin_id", "0:1")
    config.set("Settings", "api_id", '0')
    config.set("Settings", "api_hash", '0')
    config.set("Settings", "two_fa", 'gkpole')

    with open(path, "w") as config_file:
        config.write(config_file)


def check_config_file():
    if not os.path.exists(path):
        create_config()

        print('Config created')
        time.sleep(3)
        exit(0)


def config(what):
    config = configparser.ConfigParser()
    config.read(path)

    value = config.get("Settings", what)
    
    # Убираем кавычки если они есть
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    elif value.startswith("'") and value.endswith("'"):
        value = value[1:-1]

    return value


def edit_config(setting, value):
    config = configparser.ConfigParser()
    config.read(path)

    config.set("Settings", setting, value)

    with open(path, "w") as config_file:
        config.write(config_file)


check_config_file()
