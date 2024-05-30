from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, ImageSendMessage
from linebot.exceptions import LineBotApiError
import logging

logger = logging.getLogger(__name__)

class LineMessage:
    def __init__(self, channel_access_token, user_id):
        self.line_bot_api = LineBotApi(channel_access_token)
        self.user_id = user_id

    def send_textmessage(self, message):
        try:
            self.line_bot_api.push_message(self.user_id, TextSendMessage(text=message))
        except LineBotApiError as e:
            logger.error(e)

    def send_imagemessage(self, image_url):
        try:
            self.line_bot_api.push_message(self.user_id, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))
        except LineBotApiError as e:
            logger.error(e)

    def send_stickermessage(self, package_id, sticker_id):
        try:
            self.line_bot_api.push_message(self.user_id, StickerSendMessage(package_id=package_id, sticker_id=sticker_id))
        except LineBotApiError as e:
            logger.error(e)
