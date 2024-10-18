"""数据结构模块

设计和定义了API调用相关的数据结构。

Classes:
    ChatModel: 聊天模型类
    ChatHistory: 消息记录类
"""


class ChatModel:
    """聊天模型类
    
    Attributes:
        name: str 模型名称
        url: str 模型的websockets请求地址
        domain: str 模型的domain
        max_length: int 模型的最大token长度
    """
    name: str
    url: str
    domain: str
    max_length: int
    def __init__(self, name: str, url: str, domain: str, max_length: int) -> None:
        self.name = name
        self.url = url
        self.domain = domain
        self.max_length = max_length


class ChatHistory:
    """消息记录类
    
    Attributes:
        messages: list 消息列表。每个元素是一个字典，包含两个键值对，分别是"sender"和"content"，分别表示发送者和消息内容
        _msg_len: list 每条消息的长度
    
    Functions:
        __init__: 初始化方法
        __str__: 字符串方法
        trim_message: 修剪消息记录
        append_message: 追加消息

    TODO: 消息记录的持久化
    """
    messages: list
    _msg_len: list
    def __init__(self, messages: list=[]) -> None:
        self.messages = messages
        self._msg_len = [len(str(msg)) for msg in messages]

    def __str__(self) -> str:
        return str(self.messages)

    def trim_message(self, max_length: int) -> None:
        """修剪消息记录
        
        修剪消息记录，使得消息的总token长度不超过模型的最大token长度。

        Args:
            max_length: int 模型的最大token长度
        """
        while sum(self._msg_len) > max_length*1.2:
            self.messages.pop(0)
            self._msg_len.pop(0)

    def append_message(self, sender: str, content: str) -> None:
        """追加消息
        
        Args:
            sender: str 发送者。可选值："user"、"assistant"
            content: str 消息内容
        
        Raises:
            ValueError: sender不是"user"或"assistant"
        """
        if sender not in ["user", "assistant"]:
            raise ValueError("sender must be 'user' or 'assistant'")
        
        msg = {"sender": sender, "content": content}
        self.messages.append(msg)
        self._msg_len.append(len(str(msg)))

