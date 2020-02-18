import os
import requests

TOKEN = os.environ.get("TOKEN")


def turnio_googlesearch_webhook(request):
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


def turnio_googlesearch_context(request):
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

    text_messages = [m for m in json["messages"] if m["type"] == "text"]
    if text_messages:
        text = text_messages[0]["text"]["body"]
        suggested_responses = GoogleSearchClient().search(text).results
    else:
        suggested_responses = []
    return {
        "version": "1.0.0-alpha",
        "context_objects": {
            "language_region": {"Language": "Kashmiri", "Region": "Kashmir"}
        },
        "suggested_responses": [
            {
                "type": "TEXT",
                "title": f"search result {index}",
                "body": f"{result.title} {result.url}",
                "confidence": ((len(suggested_responses) - index) / 10),
            }
            for index, result in enumerate(suggested_responses)
        ],
    }


if __name__ == "__main__":
    from flask import Flask, request
    import functools

    webhooks = functools.partial(turnio_googlesearch_webhook, request)
    webhooks.__name__ = "webhooks"

    context = functools.partial(turnio_googlesearch_context, request)
    context.__name__ = "context"

    app = Flask(__name__)
    app.route("/", methods=["POST"])(webhooks)
    app.route("/context", methods=["POST"])(context)
    app.run()
