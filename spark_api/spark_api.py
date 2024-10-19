import base64
import hashlib
import hmac
import json
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode, urlparse
from wsgiref.handlers import format_date_time

import websockets
import asyncio

from data_structure import(
    ChatModel,
    ChatHistory,
    ChatParams
)
from config import(
    app_id, api_secret, api_key # API信息
)
from data import (
    chat_models,
    chat_history
)


def generate_url(url)->str:
    """生成带签名的URL

    Args:
        url: str 模型的websockets请求地址

    Returns:
        str: 带签名的URL
    """
    parsed_url = urlparse(url)
    host = parsed_url.netloc
    path = parsed_url.path
    
    # 生成RFC1123格式的时间戳
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))

    # 拼接字符串
    signature_origin = f"host: {host}\n"
    signature_origin += f"date: {date}\n"
    signature_origin += f"GET {path} HTTP/1.1"

    # 使用hmac-sha256进行加密
    def b64_sha256(key: str, msg: str) -> str:
        return base64.b64encode(
            hmac.new(
                key.encode("utf-8"),
                msg.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode(encoding="utf-8")
    signature = b64_sha256(api_secret, signature_origin)
    auth_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    auth = base64.b64encode(auth_origin.encode("utf-8")).decode("utf-8")

    # 将请求的鉴权参数组合为字典
    v = {"authorization": auth, "date": date, "host": host}
    # 拼接鉴权参数，生成url
    url = url + "?" + urlencode(v)

    return url

def gen_params(model: ChatModel, history: ChatHistory, params: ChatParams)->dict:
    """生成请求参数

    Args:
        model: ChatModel 模型
        history: ChatHistory 消息记录
        params: ChatParams 请求参数

    Returns:
        dict: 请求参数
    """
    return {
        "header": {"app_id": app_id, "uid": "CCLMSY"},
        "parameter": {
            "chat": {
                "domain": model.domain,
                "max_tokens": model.max_tokens,
                "temperature": params.temperature,
                "top_k": params.top_k
            }
        },
        "payload": {"message": {"text": history.messages}}
    }


answer: str = "" # 机器人回答，应对流式响应


async def on_message(
    ws: websockets.WebSocketClientProtocol,
    message: str | bytes,
)->None:
    """处理Websockets接收到的消息

    处理Websockets接收到的消息，将流式回复拼接为完整回复，存储在全局变量answer中。

    Args:
        ws: websockets.WebSocketClientProtocol websocket连接
        message: str | bytes 收到的Websockets消息
    
    Raises:
        Exception: SparkAPI请求错误
    """
    msg = json.loads(message)
    code = msg["header"]["code"]

    if code != 0:
        await ws.close()
        raise Exception(f"SparkAPI请求错误: Code:'{code}', Message:'{msg}'")
    
    choices = msg["payload"]["choices"]
    status = choices["status"]
    content = choices["text"][0]["content"]

    global answer
    if status == 0: # 收到首个消息，清空answer
        answer = ""
    answer += content
    if status == 2: # 收到最后一个消息，关闭连接
        await ws.close()


async def connect_ws(
    model: ChatModel,
    history: ChatHistory,
    params: ChatParams,
)->None:
    """连接到Websockets

    连接到Websockets，发送请求，接收回复并处理。

    Args:
        model: ChatModel 模型
        history: ChatHistory 消息记录
        params: ChatParams 请求参数
    """
    ws_url = generate_url(model.url)
    async with websockets.connect(ws_url) as ws:
        send_message = json.dumps(gen_params(model, history, params))
        await ws.send(send_message)
        async for message in ws:
            await on_message(ws, message)



async def request_chat(
    model: ChatModel,
    history: ChatHistory,
    params: ChatParams,
    question: str,
)->str:
    """请求聊天

    请求聊天，将用户问题发送给机器人，接收机器人回答，并更新消息记录。

    Args:
        model: ChatModel 模型
        history: ChatHistory 消息记录
        params: ChatParams 请求参数
        question: str 用户问题

    Returns:
        str: 机器人回答
    """
    global answer
    history.append_message("user", question)
    await connect_ws(model, history, params)
    history.append_message("assistant", answer)
    return answer


# 测试
# def show_chat_history(history: ChatHistory)->None:
#     """显示消息记录"""
#     for msg in history.messages:
#         print(f"{msg['role']}: {msg['content']}")

# async def main():
#     model = chat_models[5] # 4.0Ultra
#     global chat_history
#     params = ChatParams()
#     while 1:
#         question = input("Input question:")
#         if question == "history":
#             show_chat_history(chat_history)
#             continue
#         response = await request_chat(model, chat_history, params, question)
#         print("Response from assistant:", response)

# if __name__ == "__main__":
#     asyncio.run(main()) # 采用异步方式运行main函数