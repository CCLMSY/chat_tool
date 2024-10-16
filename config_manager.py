import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding {self.config_file}. Using default configuration.")
        return self.get_default_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_default_config(self):
        return {
            "log_level": "INFO",
            "proxies": None,
            "models": [
                {
                    "name": "默认GPT-4",
                    "url": "https://ngedlktfticp.cloud.sealos.io/v1/chat/completions",
                    "api_key": "sk-0pdJT29FTe0IHf7dB531C158C17b4eB0820f6e0170DcE191",
                    "model": "gpt-4o-2024-08-06"
                }
            ],
            "max_retries": 3,
            "retry_delay": 1,
            "conversation_history_limit": 100
        }

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

    def add_model(self, name, url, api_key, model):
        self.config['models'].append({
            "name": name,
            "url": url,
            "api_key": api_key,
            "model": model
        })
        self.save_config()

    def remove_model(self, name):
        self.config['models'] = [m for m in self.config['models'] if m['name'] != name]
        self.save_config()

    def get_model(self, name):
        return next((m for m in self.config['models'] if m['name'] == name), None)