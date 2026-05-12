import requests
import time
from google.transit import gtfs_realtime_pb2
from datetime import datetime

BOT_TOKEN = "8746718042:AAFG5ACr5Zz9xHMoY8S9B-tMc52yKz3ODgE"
CHAT_ID = "8314344454"

# MTA realtime feed for N/Q/R/W/F/M lines
FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"

# Herald Square station IDs
# F northbound = D18N
# N northbound = R20N

TARGET_STOPS = {
    "F": "D18N",
    "N": "R20N"
}

def get_arrivals():
    feed = gtfs_realtime_pb2.FeedMessage()

    response = requests.get(FEED_URL)
    feed.ParseFromString(response.content)

    arrivals = {
        "F": [],
        "N": []
    }

    current_time = int(time.time())

    for entity in feed.entity:
        if not entity.HasField('trip_update'):
            continue

        trip = entity.trip_update.trip

        route = trip.route_id

        if route not in TARGET_STOPS:
            continue

        target_stop = TARGET_STOPS[route]

        for stop_time in entity.trip_update.stop_time_update:
            if stop_time.stop_id == target_stop:
                if stop_time.arrival.time:
                    eta_minutes = int(
                        (stop_time.arrival.time - current_time) / 60
                    )

                    if eta_minutes >= 0:
                        arrivals[route].append(eta_minutes)

    for route in arrivals:
        arrivals[route] = sorted(arrivals[route])[:3]

    return arrivals

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, data=payload)

def main():
    arrivals = get_arrivals()

    now = datetime.now().strftime("%I:%M %p")

    message = f"34 St–Herald Sq Train Arrivals ({now})\n\n"

    for line in ["N", "F"]:
        times = arrivals[line]

        if times:
            formatted = ", ".join([f"{t} min" for t in times])
        else:
            formatted = "No realtime data"

        message += f"{line} → Queens: {formatted}\n"

    send_telegram(message)

if __name__ == "__main__":
    main()
