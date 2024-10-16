import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ChatManager:
    def __init__(self, api_client, options):
        self.api_client = api_client
        self.options = options
        self.conversations = {}
        self.paused = False
        self.current_task = None
        self.loop = asyncio.get_event_loop()
        logger.info("ChatManager initialized")
    
    async def send_message_stream(self, message, model):
        logger.info(f"Sending message with model: {model['name']}")
        if self.paused:
            logger.warning("Chat is paused")
            yield "聊天已暂停。请恢复以继续。"
            return

        if model["name"] not in self.conversations:
            self.conversations[model["name"]] = []
        
        conversation = self.conversations[model["name"]]
        conversation.append({"role": "user", "content": message})

        # Limit conversation history
        if len(conversation) > self.options.conversation_history_limit:
            conversation = conversation[-self.options.conversation_history_limit:]

        retries = 0
        while retries < self.options.max_retries:
            try:
                async for content in self._send_message_stream(conversation, model):
                    yield content
                break
            except asyncio.CancelledError:
                logger.info("Message stream cancelled")
                yield "消息流已取消。"
                break
            except Exception as e:
                logger.exception(f"Error in send_message_stream: {str(e)}")
                retries += 1
                if retries < self.options.max_retries:
                    yield f"错误: {str(e)}. 正在重试... ({retries}/{self.options.max_retries})"
                    await asyncio.sleep(self.options.retry_delay)
                else:
                    yield f"错误: {str(e)}. 已达到最大重试次数。"
                    break  # 添加这行以在达到最大重试次数后退出循环

    async def _send_message_stream(self, conversation, model):
        async for response in self.api_client.call_api_stream("openai", model["url"], {
            "model": model["model"],
            "messages": conversation,
            "stream": True
        }, model["api_key"]):
            content = self.parse_stream_response(response)
            if content:
                yield content
                if not conversation or conversation[-1]["role"] != "assistant":
                    conversation.append({"role": "assistant", "content": ""})
                conversation[-1]["content"] += content

    def parse_stream_response(self, response):
        try:
            data = json.loads(response)
            if 'choices' in data and len(data['choices']) > 0:
                delta = data['choices'][0].get('delta', {})
                content = delta.get('content', '')
                return content
            elif 'error' in data:
                logger.error(f"Received error: {data['error']}")
                return f"错误: {data['error']}"
            return ''
        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试解析多行数据
            lines = response.strip().split('\n')
            content = ''
            for line in lines:
                try:
                    if line.startswith('data: '):
                        line = line[6:]
                    if line.strip() == '[DONE]':
                        continue
                    data = json.loads(line)
                    if 'choices' in data and len(data['choices']) > 0:
                        delta = data['choices'][0].get('delta', {})
                        content += delta.get('content', '')
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON line: {line}")
            logger.debug(f"Extracted content from multiple lines: {content}")
            return content
        except Exception as e:
            logger.exception(f"Error parsing stream response: {str(e)}")
            return ''

    def pause(self):
        self.paused = True
        if self.current_task:
            self.current_task.cancel()
        logger.info("Chat paused")

    def resume(self):
        self.paused = False
        logger.info("Chat resumed")

    def interrupt(self):
        if self.current_task:
            self.current_task.cancel()
        logger.info("Chat interrupted")

    def clear_history(self, model_name):
        if model_name in self.conversations:
            self.conversations[model_name] = []
            logger.info(f"Conversation history cleared for {model_name}")
        else:
            logger.warning(f"No conversation history found for {model_name}")

    def get_last_user_message(self, model_name):
        if model_name in self.conversations:
            for message in reversed(self.conversations[model_name]):
                if message['role'] == 'user':
                    return message['content']
        return None

    def close(self):
        # 清理资源
        if self.loop.is_running():
            self.loop.stop()
        pending = asyncio.all_tasks(self.loop)
        for task in pending:
            task.cancel()
        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        self.loop.close()