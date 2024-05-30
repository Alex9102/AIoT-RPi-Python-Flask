import sys
import base64
import requests
from mimetypes import guess_type
import logging

logger = logging.getLogger(__name__)

import os

class OpenAIHelper:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    def local_image_to_data_url(self, image_path):
        # Guess the MIME type of the image based on the file extension
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        # Read and encode the image file
        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Construct the data URL
        return f"data:{mime_type};base64,{base64_encoded_data}"

    def analyze_image(self, image_path, type):
        data_url = self.local_image_to_data_url(image_path)

        if type == "yolo":
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "你是一個人工智慧助理,請分析影像來回答。"},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "請問你在圖片看到了什麼?可能發生火災的機率?請以數字回答"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
        if type == "mp":
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {"role": "system", "content": "你是一個居家保全機器人,現在保全以設定且家中無人,請分析影像來回答。"},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "請問你在圖片看到了什麼?可能發生闖空門的機率?請以數字回答"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=self.headers, json=payload)

        return response.json()["choices"][0]["message"]["content"]