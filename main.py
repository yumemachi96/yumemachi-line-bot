import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import anthropic

app = Flask(__name__)

configuration = Configuration(access_token=os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
claude_client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

SYSTEM_PROMPT = """あなたは清掃会社「夢街美装」の丁寧なスタッフです。
会社情報：
- 会社名：夢街美装
- 所在地：静岡県静岡市葵区千代田2丁目9-13
- 電話：054-298-7605
- 対応エリア：静岡市内（無料出張）※市外は出張費別途
- 受付：24時間対応
- 公式サイト：https://yumemachibisou.com

料金表（税込）：
【壁掛けエアコン】
- 1台：10,000円
- 2台セット：18,000円
- 3台目以降：1台8,000円
- 消臭抗菌コート：2,500円
- 室外機：3,000円
- 自動掃除機能付き：8,000円
- 防虫キャップ：1,000円

【業務用エアコン（天井埋め込みタイプ）】
- 1台：24,800円
- 2台セット：47,600円
- 3台目以降：1台23,000円
- 消臭抗菌コート：3,000円
- 室外機：3,000円
- 自動掃除機能付き：8,000円
- 防虫キャップ：1,000円

【キッチン・浴室・トイレ・洗面所】
- キッチン清掃：16,800円
- レンジフード清掃：16,800円
- 浴室清掃：16,800円
- 洗面所清掃：8,800円
- 追い焚き：12,000円

サービス内容：
床清掃、カーペット清掃、鏡面・ガラス清掃、高所ガラス、レンジフード・厨房、業務用・家庭用エアコン、空気触媒、外壁清掃など

お客様からの問い合わせに丁寧かつ簡潔に日本語で答えてください。
見積もりは無料です。わからないことは「担当者より折り返しご連絡いたします」と伝えてください。"""

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    response = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    reply_text = response.content[0].text
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
