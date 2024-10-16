import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextBrowser, QLineEdit, QLabel, QComboBox, QMenuBar, QMenu, QDialog, QFormLayout, QScrollBar)
from PyQt6.QtGui import QFont, QColor, QAction, QPalette, QTextCharFormat, QTextCursor, QTextBlockFormat, QClipboard, QDesktopServices
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QUrl
from api_client import APIClient
from chat_manager import ChatManager
from options import Options
import logging
import tiktoken
from markdown import markdown
import re
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

class AsyncWorker(QThread):
    def __init__(self, coro, loop):
        super().__init__()
        self.coro = coro
        self.loop = loop
        self.signals = WorkerSignals()

    def run(self):
        try:
            asyncio.set_event_loop(self.loop)
            result = self.loop.run_until_complete(self.coro)
            self.signals.finished.emit(result)
        except Exception as e:
            logger.exception(f"Error in AsyncWorker: {str(e)}")
            self.signals.finished.emit(f"Error: {str(e)}")

class ConfigDialog(QDialog):
    def __init__(self, parent=None, options=None):
        super().__init__(parent)
        self.options = options
        self.setWindowTitle("API Configuration")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # 配置名称
        self.config_name_input = QLineEdit(self)
        layout.addWidget(QLabel("配置名称:"))
        layout.addWidget(self.config_name_input)

        # 服务选择
        self.service_combo = QComboBox(self)
        self.service_combo.addItems(["OpenAI API", "自定义"])
        layout.addWidget(QLabel("服务提供商:"))
        layout.addWidget(self.service_combo)

        # API Key
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("API Key:"))
        layout.addWidget(self.api_key_input)

        # API Base URL
        self.api_base_url_input = QLineEdit(self)
        layout.addWidget(QLabel("API Base URL:"))
        layout.addWidget(self.api_base_url_input)

        # 模型名称
        self.model_name_input = QLineEdit(self)
        layout.addWidget(QLabel("模型名称:"))
        layout.addWidget(self.model_name_input)

        # 连接信号
        self.service_combo.currentIndexChanged.connect(self.on_service_changed)

        # 按钮
        button_box = QHBoxLayout()
        save_button = QPushButton("保存", self)
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消", self)
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(save_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

    def on_service_changed(self, index):
        if index == 0:  # OpenAI API
            self.api_base_url_input.setText("https://api.openai.com")
            self.api_base_url_input.setEnabled(False)
        else:  # 自定义
            self.api_base_url_input.clear()
            self.api_base_url_input.setEnabled(True)

    def get_config(self):
        return {
            "name": self.config_name_input.text(),
            "service": self.service_combo.currentText(),
            "api_key": self.api_key_input.text(),
            "api_base_url": self.api_base_url_input.text(),
            "model_name": self.model_name_input.text()
        }

class ChatGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Chat Client")
        self.setGeometry(100, 100, 900, 700)

        self.options = Options()
        self.api_client = APIClient(self.options)
        self.chat_manager = ChatManager(self.api_client, self.options)
        self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self.worker = None
        self.dark_mode = True  # 默认使用深色模式
        self.current_ai_response = ""  # 存储当前AI响应
        self.current_ai_cursor = None  # 存储AI光标位置
        self.user_message_cursor = None  # 存储用户消息的光标位置
        self.current_model_label = None  # 添加这行

        self.setup_ui()
        self.setup_menu()
        self.apply_style()

        # 使用 QTimer 来异步设置 API 客户端
        QTimer.singleShot(0, self.async_setup_api_client)

    def async_setup_api_client(self):
        asyncio.run_coroutine_threadsafe(self.setup_api_client(), self.loop)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 聊天显示区域
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.anchorClicked.connect(self.handle_anchor_clicked)
        layout.addWidget(self.chat_display)

        # 输入区域
        input_layout = QHBoxLayout()
        self.msg_entry = QLineEdit()
        self.msg_entry.setFixedHeight(50)  # 增加输入框的高度
        self.msg_entry.setFont(QFont("Arial", 12))  # 增加字体大小
        self.msg_entry.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.msg_entry)

        send_button = QPushButton("发送")
        send_button.setFixedSize(70, 50)  # 调整发送按钮的大小
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

        # 功能按钮区域
        button_layout = QHBoxLayout()
        
        retry_button = QPushButton("重试")
        retry_button.clicked.connect(self.retry_last)
        button_layout.addWidget(retry_button)
        
        interrupt_button = QPushButton("中断")
        interrupt_button.clicked.connect(self.interrupt)
        button_layout.addWidget(interrupt_button)
        
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self.clear_chat)
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)

        # 在模型选择区域添加当前模型标签
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.addItems(self.options.get_model_names())
        self.model_combo.setCurrentText(self.options.current_model['name'])  # 设置默认选中的模型
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)

        self.current_model_label = QLabel()
        self.current_model_label.setStyleSheet("color: #808080; margin-left: 10px;")
        model_layout.addWidget(self.current_model_label)

        layout.addLayout(model_layout)

        # 初始化当前模型标签
        self.update_current_model_label()

    def apply_style(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QMainWindow, QTextBrowser, QLineEdit, QPushButton, QComboBox {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                }
                QMenuBar {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                }
                QMenuBar::item:selected, QMenu::item:selected {
                    background-color: #3E3E3E;
                }
                QMenu {
                    background-color: #2D2D2D;
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #0078D4;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #1084D9;
                }
                QComboBox {
                    border: 1px solid #3E3E3E;
                }
            """)
        else:
            self.setStyleSheet("")

    def setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        clear_action = QAction('Clear Chat', self)
        clear_action.triggered.connect(self.clear_chat)
        file_menu.addAction(clear_action)
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        retry_action = QAction('Retry Last', self)
        retry_action.triggered.connect(self.retry_last)
        edit_menu.addAction(retry_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        config_action = QAction('Configure API', self)
        config_action.triggered.connect(self.configure_api)
        settings_menu.addAction(config_action)

        # Add dark mode toggle
        dark_mode_action = QAction('Toggle Dark Mode', self)
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        settings_menu.addAction(dark_mode_action)

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_style()

    async def setup_api_client(self):
        await self.api_client.setup()

    def send_message(self):
        user_input = self.msg_entry.text()
        if not user_input.strip():
            return
        self.msg_entry.clear()
        
        # 立即显示用户消息
        self.display_message(user_input, "user")
        
        self.current_ai_response = ""  # 重置当前AI响应
        self.current_ai_cursor = None  # 重置AI光标位置
        model_name = self.model_combo.currentText()

        # 清理旧的 worker
        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker.deleteLater()

        self.worker = AsyncWorker(self.process_message(user_input, model_name), self.loop)
        self.worker.signals.progress.connect(self.on_message_progress)
        self.worker.signals.finished.connect(self.on_message_finished)
        self.worker.start()

    async def process_message(self, user_input, model_name):
        model = self.options.get_model(model_name)
        if model:
            try:
                full_response = ""
                async for response in self.chat_manager.send_message_stream(user_input, model):
                    if isinstance(response, dict) and 'error' in response:
                        self.worker.signals.progress.emit(f"错误: {response['error']}")
                        return
                    full_response += response
                    self.worker.signals.progress.emit(full_response)
                return full_response
            except Exception as e:
                logger.exception(f"Error processing message: {str(e)}")
                return f"Error: {str(e)}"
        else:
            logger.error(f"Invalid model selected: {model_name}")
            return "Error: Invalid model selected"

    def on_message_progress(self, response):
        self.current_ai_response = response
        cursor = self.chat_display.textCursor()
        
        if self.current_ai_cursor is None:
            # 如果 AI 光标位置未初始化，我们需要创建一个新的 AI 消息块
            cursor.movePosition(QTextCursor.MoveOperation.End)
            block_format = QTextBlockFormat()
            block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
            cursor.insertBlock(block_format)
            cursor.insertHtml('<div style="background-color: #2D2D2D; color: #FFFFFF; border-radius: 10px; padding: 10px; margin: 5px 0; max-width: 80%; display: inline-block;">AI: ')
            self.current_ai_cursor = cursor.position()
        else:
            cursor.setPosition(self.current_ai_cursor)
        
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        formatted_message = self.format_message_with_markdown(self.current_ai_response)
        cursor.insertHtml(formatted_message)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        QApplication.processEvents()

    def on_message_finished(self, response):
        self.add_info_bar(response)

    def display_message(self, message, tag):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        block_format = QTextBlockFormat()
        block_format.setBottomMargin(20)  # 设置段落底部边距
        
        if tag == "user":
            block_format.setAlignment(Qt.AlignmentFlag.AlignRight)
            cursor.insertBlock(block_format)
            cursor.insertHtml(f'<div style="background-color: #264F78; color: #FFFFFF; border-radius: 10px; padding: 10px; margin: 5px 0; max-width: 80%; display: inline-block;">You: {message}</div><br>')
            self.user_message_cursor = cursor.position()
        elif tag == "ai":
            block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
            if self.current_ai_cursor is None:
                cursor.insertBlock(block_format)
                cursor.insertHtml('<div style="background-color: #2D2D2D; color: #FFFFFF; border-radius: 10px; padding: 10px; margin: 5px 0; max-width: 80%; display: inline-block;">AI: ')
                self.current_ai_cursor = cursor.position()
            else:
                cursor.setPosition(self.current_ai_cursor)
            
            # 使用 Markdown 渲染消息，并特殊处理代码块
            formatted_message = self.format_message_with_markdown(message)
            cursor.insertHtml(formatted_message)
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def format_message_with_markdown(self, message):
        def code_replacer(match):
            language = match.group(1) or 'text'
            code = match.group(2)
            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except ValueError:
                lexer = TextLexer()
            formatter = HtmlFormatter(style='monokai', noclasses=True)
            highlighted_code = highlight(code, lexer, formatter)
            # 添加复制按钮
            copy_button_html = f'<button onclick="copyCodeToClipboard(this)" data-code="{code}" style="margin-left: 10px;">复制代码</button>'
            return f'<pre style="background-color: #272822; padding: 10px; border-radius: 5px; overflow-x: auto;">{highlighted_code}{copy_button_html}</pre>'

        # 使用正则表达式匹配代码块
        code_block_pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
        message = code_block_pattern.sub(code_replacer, message)

        # 使用 markdown 库渲染其余部分
        html = markdown(message, extensions=['fenced_code', 'codehilite'])
        
        # 添加JavaScript代码
        html += """
        <script>
        function copyCodeToClipboard(button) {
            const code = button.getAttribute('data-code');
            navigator.clipboard.writeText(code).then(function() {
                console.log('Code copied to clipboard');
                button.textContent = '已复制';
                setTimeout(() => {
                    button.textContent = '复制代码';
                }, 2000);
            }, function(err) {
                console.error('Could not copy text: ', err);
            });
        }
        </script>
        """
        
        return html

    def add_info_bar(self, message):
        char_count = len(message.strip())
        token_count = self.count_tokens(message)
        
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()
        
        info_text = f"字数: {char_count} | Tokens: {token_count} | "
        cursor.insertHtml(f'<span style="color: #808080;">{info_text}</span>')
        
        # 创建一个可点击的"复制"链接
        cursor.insertHtml(f'<a href="copy://{len(self.current_ai_response)}" style="color: #0078D4; text-decoration: none;">复制</a>')
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def count_tokens(self, text):
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    def copy_to_clipboard(self, message):
        clipboard = QApplication.clipboard()
        clipboard.setText(message)
        self.show_temporary_message("已复制到剪贴板。")

    def show_temporary_message(self, message, duration=3000):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()
        
        success_format = QTextCharFormat()
        success_format.setForeground(QColor("#4CAF50"))  # 绿色文本for成功提示
        cursor.insertText(message, success_format)
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        
        # 使用QTimer来在指定时间后删除消息
        QTimer.singleShot(duration, lambda: self.remove_last_message())

    def remove_last_message(self):
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()  # 删除多余的换行
        self.chat_display.setTextCursor(cursor)

    def handle_anchor_clicked(self, url):
        if url.scheme() == "copy":
            try:
                # 从URL中提取消息长度，如果为空则使用整个响应
                path = url.path()
                if path and path != '/':
                    message_length = int(path[1:])
                    message_to_copy = self.current_ai_response[:message_length]
                else:
                    message_to_copy = self.current_ai_response
                self.copy_to_clipboard(message_to_copy)
            except ValueError as e:
                logger.error(f"Error parsing URL path: {e}")
                self.show_temporary_message("复制失败：无效的消息长度")
            except Exception as e:
                logger.exception(f"Unexpected error in handle_anchor_clicked: {e}")
                self.show_temporary_message("复制失败：发生未知错误")
        elif url.scheme() == "copycode":
            try:
                # 从URL中提取代码内容
                code_to_copy = url.path()[1:]  # 去掉前导斜杠
                self.copy_to_clipboard(code_to_copy)
            except Exception as e:
                logger.exception(f"Unexpected error in handle_anchor_clicked: {e}")
                self.show_temporary_message("复制代码失败：发生未知错误")
        else:
            # 对于其他类型的链接，使用默认的系统行为打开
            QDesktopServices.openUrl(url)

    def clear_chat(self):
        self.chat_display.clear()
        self.chat_manager.clear_history(self.model_combo.currentText())
        self.show_temporary_message("聊天记录已清空。")

    def retry_last(self):
        last_message = self.chat_manager.get_last_user_message(self.model_combo.currentText())
        if last_message:
            self.msg_entry.setText(last_message)
            self.send_message()

    def interrupt(self):
        self.chat_manager.interrupt()
        self.show_temporary_message("已中断当前回复。")

    def configure_api(self):
        dialog = ConfigDialog(self, self.options)
        if dialog.exec():
            config = dialog.get_config()
            self.options.add_custom_model(
                config["name"],
                config["api_base_url"],
                config["api_key"],
                config["model_name"]
            )
            self.update_model_combo()

    def update_model_combo(self):
        self.model_combo.clear()
        for model in self.options.get_models():
            self.model_combo.addItem(model['name'])
        
        # 设置当前选中的模型
        current_model = self.options.get_current_model()
        index = self.model_combo.findText(current_model['name'])
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        # 更新当前模型标签
        self.update_current_model_label()

    def on_model_changed(self, model_name):
        self.options.set_current_model(model_name)
        self.update_current_model_label()

    def update_current_model_label(self):
        current_model = self.options.get_current_model()
        if current_model:
            self.current_model_label.setText(f"当前模型: {current_model['model']}")
        else:
            self.current_model_label.setText("")

    def closeEvent(self, event):
        if self.worker:
            self.worker.quit()
            self.worker.wait()
        self.loop.stop()
        self.loop.close()
        super().closeEvent(event)

def run():
    app = QApplication(sys.argv)
    gui = ChatGUI()
    gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run()