import os
import requests
import ddg3

TOKEN = os.environ.get("TOKEN")


def search(text):
    result = ddg3.query(text)
    search_results = []
    if result.abstract.text:
        search_results.append(
            {
                "type": "TEXT",
                "body": result.abstract.text,
                "title": "Main Abstract",
                "confidence": 1.0,
            }
        )

    if result.results:
        search_results.extend(
            [
                {
                    "type": "TEXT",
                    "body": "%s - %s" % (r.text, r.url),
                    "title": "Search Result %s" % (index,),
                    "confidence": ((len(result.results) - index) / 10),
                }
                for index, r in enumerate(result.results)
            ]
        )
    return search_results


def turnio_websearch_webhook(request):
    json = request.json
    if "statuses" in json:
        return ""

    wa_id = json["contacts"][0]["wa_id"]
    [message] = json["messages"]

    if message["type"] != "text":
        return ""

    message_id = message["id"]
    text = message["text"]["body"]

    results = search(text)
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
                    ["*%(title)s*\n\n%(body)s" % result for result in results]
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


def turnio_websearch_context(request):

    json = request.json
    if json.get("handshake", False):
        return {
            "version": "1.0.0-alpha",
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

    text_messages = [
        m
        for m in json["messages"]
        if m["type"] == "text" and m["_vnd"]["v1"]["direction"] == "inbound"
    ]
    if text_messages:
        text = text_messages[0]["text"]["body"]
        results = search(text)
        print("Searching for %r returned %d results" % (text, len(results)))
    else:
        print("Most recent message was not a text message, skipping search")
        results = []
    return {
        "version": "1.0.0-alpha",
        "context_objects": {
            "language_region": {"Language": "Kashmiri", "Region": "Kashmir"}
        },
        "suggested_responses": results,
    }


if __name__ == "__main__":
    from flask import Flask, request
    import functools

    webhooks = functools.partial(turnio_websearch_webhook, request)
    webhooks.__name__ = "webhooks"

    context = functools.partial(turnio_websearch_context, request)
    context.__name__ = "context"

    app = Flask(__name__)
    app.route("/", methods=["POST"])(webhooks)
    app.route("/context", methods=["POST"])(context)
    app.run()
