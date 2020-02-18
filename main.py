import os.environ
import requests
from flask import Flask, request


TOKEN = os.environ.get("TOKEN")


app = Flask(__name__)


@app.route("/", methods=["POST"])
def webhook():
    json = request.json
    if "statuses" in json:
        return ""

    wa_id = json["contacts"][0]["wa_id"]
    message_id = json["messages"][0]["id"]
    text = json["messages"][0]["text"]["body"]

    from google_search_client.search_client import GoogleSearchClient

    results = GoogleSearchClient().search(text).results
    response = requests.post(
        url="https://whatsapp.turn.io/v1/messages",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "to": wa_id,
            "text": {
                "body": "\n\n".join(
                    [f"{result.title} {result.url}" for result in results]
                )
            },
        },
    ).json()
    print(response)

    response = requests.post(
        url=f"https://whatsapp.turn.io/v1/messages/{message_id}/labels",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.v1+json",
            "Content-Type": "application/json",
        },
        json={"labels": ["question"]},
    )
    print(response)

    return ""


@app.route("/context", methods=["POST"])
def context():
    from google_search_client.search_client import GoogleSearchClient

    json = request.json
    if json.get("handshake", False):
        return {
            "capabilities": {
                "actions": False,
                "suggested_responses": True,
                "context_objects": [
                    {
                        "title": "Language & Region",
                        "code": "language_region",
                        "type": "table",
                        "icon": "none",
                    }
                ],
            }
        }

    results = GoogleSearchClient().search("India").results
    return {
        "version": "1.0.0-alpha",
        "context_objects": {
            "language_region": {"Language": "Kashmiri", "Region": "Kashmir"}
        },
        "suggested_responses": [
            {
                "type": "TEXT",
                "title": f"seach result {index}",
                "body": f"{result.title} {result.url}",
                "confidence": 0.4,
            }
            for index, result in enumerate(results)
        ],
    }
