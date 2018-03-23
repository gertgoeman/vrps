import dateutil.parser

def split_in_batches(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]

def time_to_seconds(time):
    return (time.hour * 60 + time.minute) * 60 + time.second

def parse_time(value):
    if isinstance(value, str):
        return dateutil.parser.parse(value).time()
    elif isinstance(value, datetime.datetime):
        return value.time()
    else:
        raise ValueError("Value is in an invalid format.")
