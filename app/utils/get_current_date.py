from datetime import datetime
import pytz


def get_current_datetime_cranford():
    eastern = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern)
    formatted_datetime = current_time.strftime("%A, %B %d, %Y at %I:%M %p")
    return formatted_datetime
