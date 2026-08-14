from flask import Flask, request
import os
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

MODEL = "google/gemini-2.5-flash"

TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text
        },
        timeout=30
    )


def ask_gemini(text):
    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": text
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]


@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True)

    if not update or "message" not in update:
        return "OK", 200

    message = update["message"]

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type")

    text = message.get("text", "")

    if not text:
        return "OK", 200

    # Личная переписка
    if chat_type == "private":
        prompt = text

    # Группа
    elif chat_type in ("group", "supergroup"):

        if not text.startswith("/ask"):
            return "OK", 200

        prompt = text[4:].strip()

        if not prompt:
            send_message(
                chat_id,
                "Использование: /ask ваш вопрос"
            )
            return "OK", 200

    else:
        return "OK", 200

    try:
        answer = ask_gemini(prompt)
        send_message(chat_id, answer)

    except Exception as e:
        print("ERROR:", e)

        send_message(
            chat_id,
            "Произошла ошибка при обращении к AI."
        )

    return "OK", 200
