import pandas as pd
from datetime import datetime


def get_active_service_ids(calendar: pd.DataFrame, calendar_dates: pd.DataFrame, date_str: str) -> set[str]:
    days_map = {0: "monday", 1: "tuesday", 2: "wednesday", 3: "thursday", 4: "friday", 5: "saturday", 6: "sunday"}
    date_obj = datetime.strptime(date_str, "%Y%m%d")
    day_name = days_map[date_obj.weekday()]
    date_int = int(date_str)

    active_services = set()

    if not calendar.empty:
        mask = (
            (calendar[day_name] == 1) & 
            (calendar["start_date"].astype(int) <= date_int) & 
            (calendar["end_date"].astype(int) >= date_int)
        )
        active_services = set(calendar.loc[mask, "service_id"].astype(str))

    if not calendar_dates.empty:
        today_exceptions = calendar_dates[calendar_dates["date"].astype(int) == date_int]
        
        for _, row in today_exceptions.iterrows():
            sid = str(row["service_id"])
            exc_type = int(row["exception_type"])
            
            if exc_type == 1:
                active_services.add(sid)
            elif exc_type == 2:
                active_services.discard(sid)

    return active_services