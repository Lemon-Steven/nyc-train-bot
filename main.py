import requests
import time
from google.transit import gtfs_realtime_pb2
from datetime import datetime

# ======================
# CONFIG
# ======================

BOT_TOKEN = "8746718042:AAGrkn55kgAN1tujdTnTpF8rQwZvs15I9mw"
CHAT_ID = "8314344454"

FEED_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs"

# Herald Square stop IDs (used only as validation, not strict filtering)
HERALD_SQUARE_STOPS = {
    "N": "R20N",
    "F": "D18N"
}

# ======================
# FETCH GTFS FEED
# ======================

def fetch_feed():
    feed = gtfs_realtime_pb2.FeedMessage()

    r = requests.get(FEED_URL, timeout=10)
    r.raise_for_status()

    feed.ParseFromString(r.content)
    return feed


# ======================
# PARSE ARRIVALS
# ======================

def get_arrivals():
    feed = fetch_feed()

    arrivals = {"N": [], "F": []}
    now = int(time.time())

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        trip = entity.trip_update.trip
        route = trip.route_id

        if route not in arrivals:
            continue

        # grab ANY upcoming stop_time_update (not station-specific)
        for stop_time in entity.trip_update.stop_time_update:
            if stop_time.arrival.time:
                eta = int((stop_time.arrival.time - now) / 60)

                if eta >= 0:
                    arrivals[route].append(eta)
                    break  # only first valid prediction per train

    for r in arrivals:
        arrivals[r] = sorted(arrivals[r])[:3]

    return arrivals


# ======================
# TELEGRAM SENDER (with error visibility)
# ======================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    r = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": message
    }, timeout=10)

    print("Telegram status:", r.status_code)
    print("Telegram response:", r.text)

    # HARD FAIL if something is wrong
    r.raise_for_status()


# ======================
# MAIN
# ======================

def main():
    print("SCRIPT STARTED")

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

    print("FINAL MESSAGE:\n", message)
    print("SENDING...")

    send_telegram(message)


if __name__ == "__main__":
    main()
