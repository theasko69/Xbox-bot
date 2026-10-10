import json
import os
import urllib.request

XBL_KEY = os.environ["XBL_KEY"]
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
# Pseudos Xbox de tes potes, séparés par des virgules. Vide = tous tes amis.
WANTED = {n.strip().lower() for n in os.environ.get("FRIENDS", "").split(",") if n.strip()}
STATE_FILE = "state.json"


def get_friends():
    req = urllib.request.Request(
        "https://xbl.io/api/v2/friends",
        headers={"X-Authorization": XBL_KEY, "Accept": "application/json", "User-Agent": "xbox-bot"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("people", [])


def send(text):
    data = json.dumps({"content": text}).encode()
    req = urllib.request.Request(
        WEBHOOK, data=data, headers={"Content-Type": "application/json", "User-Agent": "xbox-bot"}
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    first_run = not os.path.exists(STATE_FILE)
    old = {} if first_run else json.load(open(STATE_FILE))
    new = {}

    for p in get_friends():
        name = p.get("gamertag", "?")
        if WANTED and name.lower() not in WANTED:
            continue
        online = p.get("presenceState") == "Online"
        game = p.get("presenceText") or ""
        new[name] = {"online": online, "game": game}

        if first_run:
            continue
        prev = old.get(name, {"online": False, "game": ""})
        if online and not prev["online"]:
            send(f"🟢 **{name}** vient de se connecter" + (f" — {game}" if game else ""))
        elif online and game and game != prev["game"]:
            send(f"🎮 **{name}** : {game}")

    json.dump(new, open(STATE_FILE, "w"))


main()
