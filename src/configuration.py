from configparser import ConfigParser
import os.path
from datetime import time
import dateutil.parser

CONFIG_FILE = "config.ini"
OPTIONS_SECTION = "options"

def load_config():
    result = {}

    if not os.path.isfile(CONFIG_FILE): return result

    config = ConfigParser()
    config.read(CONFIG_FILE)

    options = config.options(OPTIONS_SECTION)
    dct = {}
    
    for option in options:
        dct[option] = config.get(OPTIONS_SECTION, option)

    return dct

def validate_config(value):
    # service_time must be an integer
    try:
        int(value["service_time"])
    except ValueError :
        raise ValueError("Service time must be a valid whole number representing the amount of minutes it takes to perform service at 1 location.")

def save_config(value):
    validate_config(value)

    config = ConfigParser()
    config.add_section(OPTIONS_SECTION)

    for key, v in value.items():
        config.set(OPTIONS_SECTION, key, str(v))

    cfgfile = open(CONFIG_FILE,"w")
    config.write(cfgfile)
    cfgfile.close()
