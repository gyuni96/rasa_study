import asyncio
import inspect
from sanic import Sanic, Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from typing import Text, Dict, Any, Optional, Callable, Awaitable, NoReturn

import rasa.utils.endpoints
from rasa.core.channels.channel import (
    InputChannel,
    CollectingOutputChannel,
    UserMessage,
)


class IBChat(InputChannel):
    def name(self) -> Text:
        """Name of your custom channel."""
        return "ibchat"

    def blueprint(
            self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:
        custom_webhook = Blueprint(
            "custom_webhook_{}".format(type(self).__name__),
            inspect.getmodule(self).__name__,
        )

        # @custom_webhook.route("/", methods=["GET"])
        # async def health(request: Request) -> HTTPResponse:
        #     print(request)
        #     return response.json({"status": "ok"})

        @custom_webhook.route("/", methods=["POST"])
        async def receive(request: Request) -> HTTPResponse:
            print('request.json', request.json)
            headers = request.headers
            print('headers', headers)
            print('headers.Authorization', headers.get('authorization'))
            sender_id = request.json.get("sender")  # method to get sender_id
            message = request.json.get("message") if request.json.get("message") is not None else '' # method to fetch text
            input_channel = self.name()  # method to fetch input channel
            metadata = request.json.get('metadata') if request.json.get('metadata') else {}  # method to get metadata
            print('sender_id', sender_id)
            print('message', message)
            print('input_channel', input_channel)
            metadata['accessToken'] = headers.get('authorization')
            print('metadata', metadata)

            collector = CollectingOutputChannel()

            # include exception handling

            await on_new_message(
                UserMessage(
                    message,
                    collector,
                    sender_id,
                    input_channel=input_channel,
                    metadata=metadata,
                )
            )

            return response.json(collector.messages)

        return custom_webhook