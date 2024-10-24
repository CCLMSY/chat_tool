import sys
import os
import re

# 获取当前文件的目录，并将项目根目录添加到sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QObject
from spark_api import spark_api
from chat_process import error_code
from chat_process import string_to_html
import asyncio

class ProcessingModule(QObject):
    """处理模块类，用于处理聊天信息。

    Args:
        QObject : QObject类, Qt的基类, 提供信号和槽机制
        processing_finish : pyqtSignal, 处理完成的信号，在处理完成后发射
        processing_fail : pyqtSignal, 处理失败的信号，在处理失败后发射
        chat_history : ChatHistory, 聊天记录类, 用于记录聊天信息
        chat_params : ChatParams, 聊天参数类, 用于设置聊天参数 //目前前端没有设置聊天参数
        chat_model : ChatModel, 聊天模型类, 用于设置聊天模型
        format_tool : StringToHtml, 字符串转html类, 用于将字符串转换为html格式
    """
    process_finish = pyqtSignal(str)
    process_fail = pyqtSignal(str)
    
    def __init__(self):
        
        """初始化处理模块。"""
        super().__init__()
        self.chat_history = spark_api.ChatHistory()
        self.chat_params = spark_api.ChatParams()
        self.model = spark_api.chat_models[0]
        self.format_tool = string_to_html.StringToHtml()
        
    async def process(self, data: list) -> None:
        """处理数据,然后向后端发送请求，接收回复并处理，最后发射处理结果信号。

        Args:
            data: list, 前端传来的数据，包含唯一标识、模型名称、信息类型和内容。
        """
        resquest_data = self.translate(data)
        try:
            api_result = await self.resquest_chat(resquest_data)
            formatted_result = self.format_tool.translate(api_result)
            response = self.translate_result(formatted_result, data)
            self.process_finish.emit(response)
            
        except Exception as e:
            e_code = str(e).split("Code:'")[1].split("'")[0]
            #根据错误码在字典中获取错误信息
            error_message = error_code.error_codes[int(e_code)]
            self.process_fail.emit(error_message)
            
    def translate(self, data: list) -> list:
        """翻译数据,将前端传来的数据翻译成后端需要的数据格式。

        Args:
            data: list, 前端传来的数据，包含唯一标识、模型名称、信息类型和内容。
            
        return:
            res: list, 后端需要的数据格式，包含模型类型，历史记录，聊天参数，问题和唯一标识。
        """
        res = []
        model_index = int(data[1][0]) - 1
        res.append(spark_api.chat_models[model_index])
        res.append(self.chat_history)
        res.append(self.chat_params)
        res.append(data[3])
        res.append(data[0])
        
        return res
    
    async def resquest_chat(self, resquest_date: list) -> str:
        """请求聊天,向后端发送请求，接收回复的数据。
        Args:
            resquest_data: list, 后端需要的数据格式，包含模型类型，历史记录，聊天参数，问题和唯一标识。

        Returns:
            str, 机器人的回答
        """
        api_result = await spark_api.request_chat(resquest_date[0], 
                                        resquest_date[1], 
                                        resquest_date[2], 
                                        resquest_date[3])
        
        return api_result
    
    ##将处理结果转化为前端展示的格式
    def translate_result(self, formatted_result: str, data: list) -> str:
        """翻译结果,将后端返回处理过的数据翻译成前端需要的数据格式。

        Args:
            formatted_result: str, 后端返回处理过的数据，包含机器人的回答。
            data: list, 前端传来的数据，包含唯一标识、模型名称、信息类型和内容。
            
        return:
            res: str, 前端需要的数据格式，包含所使用的模型名称和机器人的回答。
        """
        response = f"回答: <br> {formatted_result}"
        response= re.sub(r'(<br>\s*)+', '<br>', response)
        return response
        

## 测试
# if __name__ == "__main__":
#     processing_module = ProcessingModule()
#     data = ["1", "模型4", "user", "你好"]
#     asyncio.run(processing_module.process(data))

