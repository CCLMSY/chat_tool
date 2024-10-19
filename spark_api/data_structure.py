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
        max_tokens: int 模型的最大token长度
    """
    def __init__(self, name: str, url: str, domain: str, max_tokens: int) -> None:
        self.name = name
        self.url = url
        self.domain = domain
        self.max_tokens = max_tokens


class ChatParams:
    """聊天参数类
    
    Attributes:
        temperature: 核采样阈值。用于决定结果随机性，取值越高随机性越强即相同的问题得到的不同答案的可能性越高。取值范围 (0，1]，默认为0.5
        top_k: 从k个候选中随机选择⼀个（⾮等概率）。平衡生成文本的质量和多样性。较小的 k 值会减少随机性，使得输出更加稳定；而较大的 k 值会增加随机性，产生更多新颖的输出。取值范围[1, 6]，默认为4

    """
    def __init__(self, temperature: float=0.5, top_k: int=4) -> None:
        self.temperature = temperature
        self.top_k = top_k


class ChatHistory:
    """消息记录类
    
    Attributes:
        messages: list 消息列表。每个元素是一个字典，包含两个键值对，分别是"role"和"content"，分别表示发送者和消息内容
        _msg_len: list 每条消息的长度
    
    Functions:
        __init__: 初始化方法
        __str__: 字符串方法
        trim_message: 修剪消息记录
        append_message: 追加消息

    TODO: 消息记录的持久化
    """
    def __init__(self, messages: list=[]) -> None:
        self.messages = messages
        self._msg_len = [len(str(msg)) for msg in messages]

    def __str__(self) -> str:
        return str(self.messages)

    def trim_message(self, max_tokens: int) -> None:
        """修剪消息记录
        
        修剪消息记录，使得消息的总token长度不超过模型的最大token长度。

        Args:
            max_tokens: int 模型的最大token长度
        """
        while sum(self._msg_len) > max_tokens*1.2:
            self.messages.pop(0)
            self._msg_len.pop(0)

    def append_message(self, role: str, content: str) -> None:
        """追加消息
        
        Args:
            role: str 发送者。可选值："user"、"assistant"
            content: str 消息内容
        
        Raises:
            ValueError: role不是"user"或"assistant"
        """
        if role not in ["user", "assistant"]:
            raise ValueError("role must be 'user' or 'assistant'")
        
        msg = {"role": role, "content": content}
        self.messages.append(msg)
        self._msg_len.append(len(str(msg)))

