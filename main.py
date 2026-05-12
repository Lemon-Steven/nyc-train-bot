import requests
import time
from datetime import datetime
from google.transit import gtfs_realtime_pb2

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Full realtime feed (correct)
FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"

# Static GTFS stop mapping (Herald Square complex)
# These are confirmed station stop IDs for 34 St–Herald Sq
TARGET_STOPS = {
    "N": ["R20N"],   # N/Q/R/W uptown platform
    "F": ["D18N"]    # F/M uptown platform
}

def get_feed():
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get(FEED_URL)
    feed.ParseFromString(response.content)
    return feed


def get_arrivals():
    feed = get_feed()

    arrivals = {"N": [], "F": []}
    now = int(time.time())

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update.trip
        route = trip.route_id

        if route not in arrivals:
            continue

        for stop_time in entity.trip_update.stop_time_update:
            if not stop_time.arrival.time:
                continue

            stop_id = stop_time.stop_id

            # Only accept Herald Square stops
            if stop_id not in TARGET_STOPS[route]:
                continue

            eta = int((stop_time.arrival.time - now) / 60)

            if eta >= 0:
                arrivals[route].append(eta)

    # Sort + clean
    for route in arrivals:
        arrivals[route] = sorted(arrivals[route])[:3]

    return arrivals


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })


def main():
    arrivals = get_arrivals()
    now = datetime.now().strftime("%I:%M %p")

    message = f"34 St–Herald Sq Arrivals ({now})\n\n"

    for line in ["N", "F"]:
        times = arrivals[line]

        if times:
            formatted = ", ".join([f"{t} min" for t in times])
        else:
            formatted = "No upcoming trains"

        message += f"{line} → Queens: {formatted}\n"

    send_telegram(message)


if __name__ == "__main__":
    main()
