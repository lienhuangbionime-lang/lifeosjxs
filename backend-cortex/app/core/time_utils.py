from datetime import datetime
import pytz

# Set global timezone
TAIPEI_TZ = pytz.timezone('Asia/Taipei')

def get_current_time_taipei() -> datetime:
    """Returns current time in Asia/Taipei timezone."""
    return datetime.now(TAIPEI_TZ)

def get_today_str_taipei() -> str:
    """Returns YYYY-MM-DD string for today in Taipei."""
    return get_current_time_taipei().strftime('%Y-%m-%d')

def get_current_iso_taipei() -> str:
    """Returns ISO 8601 string with timezone info."""
    return get_current_time_taipei().isoformat()
