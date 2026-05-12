import requests
import time
from google.transit import gtfs_realtime_pb2
from datetime import datetime

BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Full MTA realtime feed (correct one)
FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"

def get_arrivals():
    feed = gtfs_realtime_pb2.FeedMessage()

    response = requests.get(FEED_URL)
    feed.ParseFromString(response.content)

    arrivals = {"N": [], "F": []}
    current_time = int(time.time())

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update.trip
        route = trip.route_id

        # Only N and F trains
        if route not in arrivals:
            continue

        for stop_time in entity.trip_update.stop_time_update:
            if stop_time.arrival.time:
                eta_minutes = int((stop_time.arrival.time - current_time) / 60)

                if eta_minutes >= 0:
                    arrivals[route].append(eta_minutes)
                    break  # take next upcoming stop only

    # Sort and limit results
    for route in arrivals:
        arrivals[route] = sorted(arrivals[route])[:3]

    return arrivals


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    })


def main():
    arrivals = get_arrivals()

    now = datetime.now().strftime("%I:%M %p")

    message = f"34 St–Herald Sq Train Arrivals ({now})\n\n"

    for line in ["N", "F"]:
        times = arrivals[line]

        if times:
            formatted = ", ".join([f"{t} min" for t in times])
        else:
            formatted = "No real-time data"

        message += f"{line} → Queens: {formatted}\n"

    send_telegram(message)


if __name__ == "__main__":
    main()
