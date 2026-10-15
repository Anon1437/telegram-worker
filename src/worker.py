
from js import fetch
from workers import WorkerEntrypoint, Response
import json


async def telegram(env, method, data):

    bot_token = env.BOT_TOKEN

    url = f"https://api.telegram.org/bot{bot_token}/{method}"

    response = await fetch(
        url,
        {
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps(data)
        }
    )

    return await response.json()



async def check_member(env, channel, user_id):

    result = await telegram(
        env,
        "getChatMember",
        {
            "chat_id": f"@{channel}",
            "user_id": user_id
        }
    )

    if not result.get("ok"):
        return False

    return result["result"]["status"] not in [
        "left",
        "kicked"
    ]



def keyboard(env):

    return {
        "inline_keyboard": [
            [
                {
                    "text": "Join Channel 1",
                    "url": f"https://t.me/{env.CHANNEL_1}"
                }
            ],
            [
                {
                    "text": "Join Channel 2",
                    "url": f"https://t.me/{env.CHANNEL_2}"
                }
            ],
            [
                {
                    "text": "Verify",
                    "callback_data": "verify"
                }
            ]
        ]
    }



async def send_message(env, chat_id, text, markup=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if markup:
        data["reply_markup"] = markup

    return await telegram(
        env,
        "sendMessage",
        data
    )



async def verify_user(env, chat_id, user_id):

    joined1 = await check_member(
        env,
        env.CHANNEL_1,
        user_id
    )

    joined2 = await check_member(
        env,
        env.CHANNEL_2,
        user_id
    )


    if joined1 and joined2:

        await send_message(
            env,
            chat_id,
            "✅ Verified. Access granted."
        )

    else:

        await send_message(
            env,
            chat_id,
            "❌ Not verified.\nJoin both channels then press Verify.",
            keyboard(env)
        )



class Default(WorkerEntrypoint):

    async def fetch(self, request):

        env = self.env


        if request.method == "GET":

            return Response(
                "Bot Running"
            )


        update = await request.json()


        # Normal message
        if "message" in update:

            msg = update["message"]

            await verify_user(
                env,
                msg["chat"]["id"],
                msg["from"]["id"]
            )


        # Callback button
        if "callback_query" in update:

            query = update["callback_query"]


            await telegram(
                env,
                "answerCallbackQuery",
                {
                    "callback_query_id": query["id"]
                }
            )


            if query["data"] == "verify":

                await verify_user(
                    env,
                    query["message"]["chat"]["id"],
                    query["from"]["id"]
                )


        return Response("ok")