import dateutil.parser
import datetime
import collections
import utils

TimeWindow = collections.namedtuple("TimeWindow", ["start", "end"])

def get_address_from_entry(entry, default_country):
    result = ""

    if "street" in entry:
        result = result + str(entry["street"]) + " "
    if "nr" in entry:
        result = result + str(entry["nr"]) + " "
    if "bus" in entry:
        result = result + str(entry["bus"]) + " "
    if "postal code" in entry:
        result = result + str(entry["postal code"]) + " "
    if "city" in entry:
        result = result + str(entry["city"]) + " "
    if "state" in entry:
        result = result + str(entry["state"]) + " "
    if "country" in entry:
        result = result + str(entry["country"]) + " "
    else:
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
