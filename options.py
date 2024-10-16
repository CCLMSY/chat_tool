from config_manager import ConfigManager

class Options:
    def __init__(self):
        self.api_key = "sk-0pdJT29FTe0IHf7dB531C158C17b4eB0820f6e0170DcE191"
        self.models = [
            {"name": "GPT-3.5-Turbo", "model": "gpt-3.5-turbo", "url": "https://api.openai.com/v1/chat/completions"},
            {"name": "GPT-4", "model": "gpt-4", "url": "https://api.openai.com/v1/chat/completions"},
            {"name": "测试用配置", "model": "glm-4", "url": "https://ngedlktfticp.cloud.sealos.io/v1/chat/completions", "api_key": "sk-qTr55uCegonMkaVi945a02FbE14b4c58A53cEaA5E1Ca3007"}
        ]
        self.current_model = self.models[2]  # 设置默认配置为当前模型
        self.conversation_history_limit = 10
        self.max_retries = 3
        self.retry_delay = 1
        self.proxies = None

    def get_api_key(self):
        return self.api_key

    def set_api_key(self, api_key):
        self.api_key = api_key

    def get_models(self):
        return self.models

    def get_model(self, name):
        for model in self.models:
            if model['name'] == name:
                return model
        return None

    def set_model(self, name, url):
        model = self.get_model(name)
        if model:
            model['url'] = url
        else:
            self.models.append({"name": name, "model": name, "url": url})
        self.current_model = self.get_model(name)

    def get_current_model(self):
        return self.current_model

    def set_current_model(self, name):
        model = self.get_model(name)
        if model:
            self.current_model = model

    def get_model_names(self):
        return [model['name'] for model in self.models]

    def add_custom_model(self, name, api_base_url, api_key, model_name):
        new_model = {
            "name": name,
            "model": model_name,
            "url": f"{api_base_url}/v1/chat/completions",
            "api_key": api_key
        }
        self.models.append(new_model)
        self.current_model = new_model