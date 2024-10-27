import asyncio
from spark_api.spark_api import request_chat
from spark_api.data import chat_models,chat_history,chat_params

# 测试每个模型是否能够正常运行
class Test0Class():
    def testcase_0(self):
        resp = asyncio.run(request_chat(chat_models[0], chat_history, chat_params, "你好"))
        assert resp

    def testcase_1(self):
        resp = asyncio.run(request_chat(chat_models[1], chat_history, chat_params, "你好"))
        assert resp
    
    def testcase_2(self):
        resp = asyncio.run(request_chat(chat_models[2], chat_history, chat_params, "你好"))
        assert resp
    
    def testcase_3(self):
        resp = asyncio.run(request_chat(chat_models[3], chat_history, chat_params, "你好"))
        assert resp
    
    def testcase_4(self):
        resp = asyncio.run(request_chat(chat_models[4], chat_history, chat_params, "你好"))
        assert resp
    
    def testcase_5(self):
        resp = asyncio.run(request_chat(chat_models[5], chat_history, chat_params, "你好"))
        assert resp