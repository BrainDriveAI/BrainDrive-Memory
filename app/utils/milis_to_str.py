from datetime import datetime

def millis_to_str(ms):
    # assuming ms is an integer milliseconds since epoch
    return datetime.fromtimestamp(ms / 1_000).strftime("%Y-%m-%d %H:%M:%S")
