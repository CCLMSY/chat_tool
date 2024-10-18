"""数据模块

该模块包含了存储数据相关的对象和变量，包括：
chat_models: 聊天模型列表
chat_history: 消息记录
"""

from .data_structure import(
    ChatModel,
    ChatHistory
)

chat_models = [
    ChatModel("Spark Lite", "wss://spark-api.xf-yun.com/v1.1/chat", "lite", 4096),
    ChatModel("Spark Pro", "wss://spark-api.xf-yun.com/v3.1/chat", "generalv3", 8192),
    ChatModel("Spark Pro-128K", " wss://spark-api.xf-yun.com/chat/pro-128k", "pro-128k", 4096),
    ChatModel("Spark Max", "wss://spark-api.xf-yun.com/v3.5/chat", "generalv3.5", 8192),
    ChatModel("Spark Max-32K", "wss://spark-api.xf-yun.com/chat/max-32k", "max-32k", 8192),
    ChatModel("Spark4.0 Ultra", "wss://spark-api.xf-yun.com/v4.0/chat", "4.0Ultra", 8192)
] 
"""list: 聊天模型列表"""

chat_history = ChatHistory()
"""ChatHistory: 消息记录"""