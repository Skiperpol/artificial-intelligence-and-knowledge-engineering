GTFS_DTYPES: dict[str, dict[str, str]] = {
    "stops": {
        "stop_id": "string",
        "stop_name": "string",
        "stop_lat": "float64",
        "stop_lon": "float64",
        "parent_station": "string",
    },
    "stop_times": {
        "trip_id": "string",
        "arrival_time": "string",
        "departure_time": "string",
        "stop_id": "string",
        "stop_sequence": "int32",
        "pickup_type": "int8",
    },
    "trips": {
        "trip_id": "string",
        "route_id": "string",
        "service_id": "string",
    },
    "routes": {
        "route_id": "string",
        "route_short_name": "string",
        "route_long_name": "string",
    },
    "calendar": {
        "service_id": "string",
        "monday": "int8",
        "tuesday": "int8",
        "wednesday": "int8",
        "thursday": "int8",
        "friday": "int8",
        "saturday": "int8",
        "sunday": "int8",
        "start_date": "int32",
        "end_date": "int32",
    },
    "calendar_dates": {
        "service_id": "string",
        "date": "int32",
        "exception_type": "int8",
    },
}
