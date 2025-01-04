from datetime import datetime, UTC

def format_timestamp(timestamp: str) -> str:
    try:
        # ISO format
        if 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        # YYYY-MM-DD HH:MM:SS UTC format
        else:
            dt = datetime.strptime(timestamp.replace(' UTC', ''), '%Y-%m-%d %H:%M:%S')
            dt = dt.replace(tzinfo=UTC)
            
        return dt.strftime('%Y-%m-%d %H:%M UTC')
    except (ValueError, AttributeError):
        return timestamp