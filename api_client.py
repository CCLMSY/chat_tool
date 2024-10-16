import aiohttp
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, options):
        self.options = options
        self.session = None
        logger.info("APIClient initialized")
    
    async def setup(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        logger.info("APIClient setup")
    
    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("APIClient session closed")
    
    async def call_api_stream(self, service, endpoint, data, api_key):
        logger.info(f"Calling API stream for service: {service}")
        await self.setup()  # Ensure session is set up
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        try:
            async with self.session.post(endpoint, json=data, headers=headers, proxy=self.options.proxies, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    logger.info("API call successful")
                    async for line in response.content.iter_any():
                        if line:
                            try:
                                line = line.decode('utf-8').strip()
                                if line.startswith('data: '):
                                    line = line[6:]
                                if line and line != '[DONE]':
                                    yield line
                            except UnicodeDecodeError:
                                logger.warning(f"Failed to decode line: {line}")
                else:
                    error_text = await response.text()
                    logger.error(f"API call failed with status {response.status}: {error_text}")
                    yield json.dumps({"error": f"API调用失败，状态码: {response.status}, 错误: {error_text}"})
        except asyncio.TimeoutError:
            logger.exception("API call timed out")
            yield json.dumps({"error": "API调用超时"})
        except aiohttp.ClientError as e:
            logger.exception(f"API call failed: {str(e)}")
            yield json.dumps({"error": f"API调用失败: {str(e)}"})

    def set_api_key(self, service, api_key):
        logger.info(f"Setting API key for service: {service}")
        # 这个方法可能需要根据实际需求进行修改
        pass