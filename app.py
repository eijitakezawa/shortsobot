from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent
from linebot.v3.messaging.models import TextMessage as EventTextMessage
import openai
import os

app = Flask(__name__)

configuration = Configuration(access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
line_bot_api = MessagingApi(configuration)
handler = WebhookHandler(channel_secret=os.environ["LINE_CHANNEL_SECRET"])
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=EventTextMessage)
def handle_message(event):
    user_input = event.message.text

    prompt = f'以下の短所を、前向きな長所に言い換えてください。やさしく肯定的な言葉でお願いします。\n\n短所：「{user_input}」'

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.7,
    )

    reply = response.choices[0].message['content'].strip()

    line_bot_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text=reply)]
        )
    )
