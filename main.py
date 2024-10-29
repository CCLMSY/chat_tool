"""AI Chat Client

该模块提供一个简单的聊天界面，用户可以通过输入框与模拟AI进行对话。
聊天界面包括发送消息、选择模型、清空聊天记录等功能。
"""
import asyncio
from qasync import QEventLoop
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QTextBrowser, QComboBox, QMenuBar, QWidgetAction
)
from PyQt6.QtGui import QFont, QTextCursor, QTextBlockFormat, QTextCharFormat, QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from chat_process.chat_process import ProcessingModule


class ChatGui(QMainWindow):
    """聊天界面类，用于与用户交互并处理聊天信息。

    Attributes:
        send_data_signal: 用于向处理模块发送数据的信号。
        timeout_signal: 超时信号，用于在处理模块超时时触发。
        current_model: 当前选中的模型。
        data_structure: 记录发送的消息数据。
        allow_send: 控制是否允许发送消息。
        processing_message_id: 当前处理消息的唯一标识。
        processing_block_position: 记录"正在处理中..."消息的位置。
    """
    send_data_signal = pyqtSignal(list)
    timeout_signal = pyqtSignal(str)

    def __init__(self):
        """初始化聊天界面。"""
        super().__init__()
        self.setWindowTitle("AI Chat Client")
        self.setGeometry(800, 450, 800, 600)

        self.current_model = "1.Spark Lite"
        self.data_structure = []
        self.allow_send = True
        self.processing_message_id = None
        self.processing_block_position = 0

        self.processing_module = ProcessingModule()

        self._setup_ui()
        self._setup_signals()
        self._setup_menu()

    def _setup_ui(self):
        """设置界面元素，包括聊天显示区和输入区。"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.chat_display = QTextBrowser()
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.msg_entry = QTextEdit(self)
        self.msg_entry.setFixedHeight(50)
        self.msg_entry.setFont(QFont("Arial", 12))
        input_layout.addWidget(self.msg_entry)

        self.send_button = QPushButton("发送")
        self.send_button.setFixedSize(70, 50)
        self.send_button.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

    ##因为processing_module.process是一个异步函数，所以需要在这里设置信号与处理方法的连接
    async def _process(self, data: list):
        """异步处理数据"""
        await self.processing_module.process(data)

    def _setup_signals(self):
        """设置信号与处理方法的连接。"""
        self.processing_module.process_finish.connect(self._on_process_finish)
        self.processing_module.process_fail.connect(self._on_process_fail)
        self.send_data_signal.connect(lambda data: asyncio.create_task(self._process(data)))
        self.timeout_signal.connect(self._on_process_fail)

    def _setup_menu(self):
        """设置菜单栏，包括文件、编辑和设置菜单。"""
        menubar = self.menuBar()
        if not menubar:
            raise ValueError("No menu bar found.")

        file_menu = menubar.addMenu('文件')
        if not file_menu:
            raise ValueError("Failed to create file menu.")

        exit_action = QAction('退出', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu('编辑')
        if not edit_menu:
            raise ValueError("Failed to create edit menu.")
        clear_action = QAction('清空', self)
        clear_action.triggered.connect(self._clear_chat)
        edit_menu.addAction(clear_action)

        settings_menu = menubar.addMenu('设置')
        if not settings_menu:
            raise ValueError("Failed to create settings menu.")
        self.model_combo = QComboBox(self)
        self.model_combo.addItems(["1.Spark Lite", "2.Spark Pro", "3.Spark Pro-128K", "4.Spark Max", "5.Spark Max-32K", "6.Spark4.0 Ultra"])
        self.model_combo.setCurrentIndex(0)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        model_widget = QWidget(self)
        model_layout = QVBoxLayout(model_widget)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.addWidget(self.model_combo)

        model_action = QWidgetAction(self)
        model_action.setDefaultWidget(model_widget)
        settings_menu.addAction(model_action)

    def _on_model_changed(self):
        """更新当前选中的模型，并显示提示消息。"""
        self.current_model = self.model_combo.currentText()
        self._display_message(f"已切换到 {self.current_model}", "system")

    def _send_message(self):
        """处理发送消息的逻辑，包括显示用户消息和发送数据给处理模块。"""
        if not self.allow_send:
            return

        user_input = self.msg_entry.toPlainText().strip()
        if not user_input:
            return

        self._display_message(user_input, "user")
        self.msg_entry.clear()

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.data_structure = [timestamp, self.current_model, "text", user_input]
        self.processing_message_id = timestamp

        self.allow_send = False
        self.send_button.setEnabled(False)

        # 记录“正在处理中...”的位置，以便后续替换
        self.processing_block_position = self._display_message("正在处理中...", "processing")

        # 所发送的信号即为
        self.send_data_signal.emit(self.data_structure)
        self._start_timeout_timer(100000, timestamp)

    def _start_timeout_timer(self, timeout_duration: int, timestamp: str):
        """启动超时计时器。

        Args:
            timeout_duration: 超时时间（毫秒）。
            timestamp: 当前消息的唯一标识符。
        """
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.timeout.connect(lambda: self.timeout_signal.emit(timestamp))
        self.timeout_timer.start(timeout_duration)

    def _stop_timeout_timer(self):
        """停止超时计时器。"""
        if hasattr(self, 'timeout_timer') and self.timeout_timer.isActive():
            self.timeout_timer.stop()

    @pyqtSlot(str)
    def _on_process_finish(self, response: str):
        """处理处理模块成功返回的结果。

        Args:
            response: 处理模块返回的消息内容。
        """
        self._replace_processing_message(response)
        self.allow_send = True
        self.send_button.setEnabled(True)
        self._stop_timeout_timer()

    @pyqtSlot(str)
    def _on_process_fail(self, error: str):
        """处理处理模块失败的情况。

        Args:
            code: 错误信息,有可能是API调用返回错误状态也可能是当前消息的唯一标识符。
        """
        if error == self.processing_message_id:
            self._replace_processing_message("处理超时，请重试。", is_error=True)
            self.allow_send = True
            self.send_button.setEnabled(True)
            self._stop_timeout_timer()
        else:
            self._replace_processing_message(error, is_error=True)
            self.allow_send = True
            self.send_button.setEnabled(True)
            self._stop_timeout_timer()
            
    def _display_message(self, message: str, tag: str) -> int:
        """显示消息到聊天显示区。

        Args:
            message: 要显示的消息内容。
            tag: 消息的类型（user, processing, ai, system）。

        Returns:
            int: 消息块的位置。
        """
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        block_format = QTextBlockFormat()
        char_format = QTextCharFormat()
        char_format.setFont(QFont("Arial", 12))

        formatted_message=""
        if tag == "user":
            block_format.setAlignment(Qt.AlignmentFlag.AlignRight)
            formatted_message = f"<b>你</b><br>{message}"
        elif tag in ["processing", "ai"]:
            block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
            formatted_message = f"<b>{self.current_model}</b><br>{message}"
        elif tag == "system":
            block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
            formatted_message = f"<i>{message}</i>"

        cursor.insertBlock(block_format, char_format)
        cursor.insertHtml(formatted_message)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

        return cursor.block().position()

    def _replace_processing_message(self, new_message: str, is_error: bool = False):
        """替换“正在处理中...”的消息内容。

        Args:
            new_message: 要替换的内容。
            is_error: 是否为错误消息。
        """
        cursor = self.chat_display.textCursor()
        cursor.setPosition(self.processing_block_position)

        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        char_format = QTextCharFormat()
        char_format.setFont(QFont("Arial", 12))

        if is_error:
            char_format.setForeground(Qt.GlobalColor.red)
            formatted_message = f"<b>{self.current_model}</b><br><span style='color:red;'>{new_message}</span>"
        else:
            formatted_message = f"<b>{self.current_model}</b>{new_message}"

        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.insertBlock(block_format, char_format)
        temp = f"<div style='text-align: left;'>{formatted_message}</div>"
        cursor.insertHtml(f"<div style='text-align: left;'>{formatted_message}</div>")
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def _clear_chat(self):
        """清空聊天记录。"""
        self.chat_display.clear()


#----------------以下是模拟处理模块
# class ProcessingModule(QObject):
#     """处理模块，用于模拟与AI的交互。

#     Attributes:
#         process_finish: 处理成功信号。
#         process_fail: 处理失败信号。
#     """
#     process_finish = pyqtSignal(str)
#     process_fail = pyqtSignal(str)

#     def process(self, data: list):
#         """模拟处理数据并返回结果。

#         Args:
#             data: 发送的数据列表，包含唯一标识、模型名称、信息类型和内容。
#         """
#         QTimer.singleShot(1000, lambda: self._mock_process(data))

#     def _mock_process(self, data: list):
#         """模拟处理逻辑，直接返回处理结果。

#         Args:
#             data: 发送的数据列表，包含唯一标识、模型名称、信息类型和内容。
#         """
#         unique_id, model, msg_type, content = data
#         response = f"Received: {content} using model {model}"
#         self.process_finish.emit(response)


async def main():
    """程序入口，启动聊天界面应用。"""
    app = QApplication(sys.argv)
    gui = ChatGui()
    gui.show()
    loop = QEventLoop(app) 
    asyncio.set_event_loop(loop) # 设置事件循环
    with loop:
        await loop.run_forever() # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
