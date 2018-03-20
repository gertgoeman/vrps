import dateutil.parser
import datetime
import collections
import utils

TimeWindow = collections.namedtuple("TimeWindow", ["start", "end"])

def get_address_from_entry(entry, default_country):
    result = ""

    if "address" in entry:
        result = result + str(entry["address"]) + " "
    if "postal code" in entry:
        result = result + str(entry["postal code"]) + " "
    if "city" in entry:
        result = result + str(entry["city"]) + " "
    
    result = result + default_country + " "

    return result.rstrip()

def get_time_window_from_entry(entry):
    if "start time" not in entry: raise ValueError("Start time not in entry.")
    if "end time" not in entry: raise ValueError("End time not in entry.")

    start_time = entry["start time"]
    end_time = entry["end time"]

    return TimeWindow(
        utils.time_to_seconds(utils.parse_time(start_time)), 
        utils.time_to_seconds(utils.parse_time(end_time)))
