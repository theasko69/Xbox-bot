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
        return json.load(r)


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

    data = get_friends()
    # OpenXBL enveloppe parfois la réponse dans {"content": ..., "code": ...}
    if isinstance(data, dict) and "content" in data:
        data = data["content"]
    if isinstance(data, str):
        data = json.loads(data)
    people = data.get("people", []) if isinstance(data, dict) else data
    print(len(people), "amis reçus de OpenXBL")
    if not people and os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        # Diagnostic envoyé sur Discord (pas dans les logs publics)
        if isinstance(data, dict):
            infos = {k: (f"liste de {len(v)}" if isinstance(v, list) else str(v)[:150]) for k, v in data.items()}
        else:
            infos = str(type(data))
        send(f"🔎 Réponse OpenXBL : {infos}")

    for p in people:
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

    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        en_ligne = [n for n, v in new.items() if v["online"]]
        send(
            f"✅ Bot actif : {len(people)} amis reçus, {len(new)} suivis, "
            f"{len(en_ligne)} connectés ({', '.join(en_ligne) or 'personne'})"
        )


main()
