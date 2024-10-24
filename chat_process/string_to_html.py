import re
"""str格式转换html模块

该模块用于将str格式的聊天内容转换为html格式，以便在前端展示。
"""

class StringToHtml:
    """将str格式的聊天内容转换为html格式。

    """

    def translate(self, response:str)->str:
        """翻译聊天内容,将str格式的聊天内容翻译为html格式。
        
        Args:
        response: str，str格式的聊天内容
        
        Returns:
            str, html格式的聊天内容
        """
        response = response.replace("\n", "<br>")
        response = response.replace("```", "<code>", 1)
        response = response.replace("```", "</code>", 1)
        response= re.sub(r'(<br>\s*)+', '<br>', response)
        response = re.sub(r'</code><br>', '</code>', response)
        return response
        