import sys
import os
import time
import psutil
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QLineEdit, QRadioButton, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# 关机线程（定时或steam）
class ShutdownThread(QThread):
    update_status = pyqtSignal(str)
    update_countdown = pyqtSignal(str)  # 新增倒计时信号
    trigger_shutdown = pyqtSignal()

    def __init__(self, mode, minutes=None):
        super().__init__()
        self.mode = mode
        self.minutes = minutes
        self._running = True

    def run(self):
        if self.mode == "timer":
            if self.minutes is None or self.minutes <= 0:
                self.update_status.emit("无效的分钟数")
                return
                
            self.update_status.emit(f"{self.minutes} 分钟后将自动关机")
            total_seconds = self.minutes * 60
            
            for i in range(total_seconds):
                if not self._running:
                    self.update_status.emit("已取消定时关机")
                    self.update_countdown.emit("")
                    return
                
                remaining_seconds = total_seconds - i
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                
                # 更新倒计时显示
                countdown_text = f"剩余时间: {remaining_minutes:02d}:{remaining_secs:02d}"
                self.update_countdown.emit(countdown_text)
                
                # 每秒检查一次停止标志
                time.sleep(1)
            
            # 最终检查，防止在sleep期间被取消
            if not self._running:
                self.update_status.emit("已取消定时关机")
                self.update_countdown.emit("")
                return
                
            self.update_countdown.emit("时间到！")
            self.trigger_shutdown.emit()

        elif self.mode == "steam":
            self.update_status.emit("开始检测 Steam 下载状态...")
            idle_time_limit = 120  # 改为3分钟
            check_interval = 5
            
            # 检查Steam进程
            steam_proc = self.get_steam_process()
            if not steam_proc:
                self.update_status.emit("未检测到 Steam 进程，请确保Steam正在运行")
                self.update_countdown.emit("")
                return

            self.update_status.emit(f"检测到Steam进程: {steam_proc.name()}")
            
            # 获取初始网络和磁盘IO数据
            try:
                # 获取网络接口流量
                net_io = psutil.net_io_counters()
                last_bytes_recv = net_io.bytes_recv
                last_bytes_sent = net_io.bytes_sent
                
                # 获取磁盘IO数据
                disk_io = psutil.disk_io_counters()
                if disk_io is None:
                    self.update_status.emit("无法获取磁盘IO信息，将只监控网络活动")
                    last_read_bytes = 0
                    last_write_bytes = 0
                else:
                    last_read_bytes = disk_io.read_bytes
                    last_write_bytes = disk_io.write_bytes
                
            except Exception as e:
                self.update_status.emit(f"无法获取系统IO信息: {str(e)}")
                self.update_countdown.emit("")
                return

            idle_seconds = 0
            self.update_status.emit("开始监控网络和磁盘活动...")

            while self._running:
                # 使用更短的sleep间隔，更频繁地检查停止标志
                for _ in range(check_interval):
                    if not self._running:
                        self.update_status.emit("已取消监控")
                        self.update_countdown.emit("")
                        return
                    time.sleep(1)
                
                # 再次检查停止标志
                if not self._running:
                    self.update_status.emit("已取消监控")
                    self.update_countdown.emit("")
                    return
                
                # 检查Steam进程是否还在运行
                if not steam_proc.is_running():
                    self.update_status.emit("Steam 进程已关闭")
                    self.update_countdown.emit("")
                    return
                
                try:
                    # 获取当前网络流量
                    net_io = psutil.net_io_counters()
                    current_bytes_recv = net_io.bytes_recv
                    current_bytes_sent = net_io.bytes_sent
                    
                    # 获取当前磁盘IO
                    disk_io = psutil.disk_io_counters()
                    if disk_io is None:
                        current_read_bytes = 0
                        current_write_bytes = 0
                    else:
                        current_read_bytes = disk_io.read_bytes
                        current_write_bytes = disk_io.write_bytes
                    
                    # 计算速度 (KB/s)
                    download_speed = (current_bytes_recv - last_bytes_recv) / check_interval / 1024
                    upload_speed = (current_bytes_sent - last_bytes_sent) / check_interval / 1024
                    read_speed = (current_read_bytes - last_read_bytes) / check_interval / 1024
                    write_speed = (current_write_bytes - last_write_bytes) / check_interval / 1024
                    
                    # 更新上次的数据
                    last_bytes_recv = current_bytes_recv
                    last_bytes_sent = current_bytes_sent
                    last_read_bytes = current_read_bytes
                    last_write_bytes = current_write_bytes

                    # 格式化速度显示，添加单位
                    def format_speed(speed):
                        if speed >= 1024:
                            return f"{speed/1024:.1f} MB/s"
                        else:
                            return f"{speed:.1f} KB/s"
                    
                    # 显示所有活动信息
                    status_text = f"网络: ↓{format_speed(download_speed)} ↑{format_speed(upload_speed)} | 磁盘: 读{format_speed(read_speed)} 写{format_speed(write_speed)}"
                    self.update_status.emit(status_text)

                    # 网络和磁盘活跃计数器
                    if not hasattr(self, 'disk_active_count'):
                        self.disk_active_count = 0
                    if not hasattr(self, 'network_active_count'):
                        self.network_active_count = 0
                    required_active_count = 3  # 3秒

                    # 网络阈值
                    network_active = download_speed > 100 or upload_speed > 100
                    # 磁盘阈值
                    disk_active = read_speed > 1024 or write_speed > 1024

                    # 网络活跃计数
                    if network_active:
                        self.network_active_count += 1
                        if self.network_active_count >= required_active_count:
                            idle_seconds = 0
                    else:
                        self.network_active_count = 0

                    # 磁盘活跃计数
                    if disk_active:
                        self.disk_active_count += 1
                        if self.disk_active_count >= required_active_count:
                            idle_seconds = 0
                    else:
                        self.disk_active_count = 0

                    # 只有都不活跃时才累加idle_seconds
                    if not network_active and not disk_active:
                        idle_seconds += check_interval

                    # 显示空闲计时
                    remaining_idle = idle_time_limit - idle_seconds
                    if remaining_idle > 0:
                        # 转换为分钟和秒显示
                        remaining_minutes = remaining_idle // 60
                        remaining_secs = remaining_idle % 60
                        countdown_text = f"活动停止计时: {remaining_minutes}分{remaining_secs}秒后关机"
                    else:
                        countdown_text = "准备关机..."

                    self.update_countdown.emit(countdown_text)

                    if idle_seconds >= idle_time_limit:
                        self.update_status.emit("Steam活动完全停止，准备关机")
                        self.update_countdown.emit("准备关机...")
                        self.trigger_shutdown.emit()
                        return
                        
                except Exception as e:
                    self.update_status.emit(f"监控出错: {str(e)}")
                    self.update_countdown.emit("监控出错")
                    return

    def stop(self):
        """停止线程执行"""
        self._running = False
        # 等待线程结束，但最多等待2秒
        if self.isRunning():
            self.wait(2000)  # 等待2秒
            if self.isRunning():
                self.terminate()  # 强制终止
                self.wait(1000)   # 再等待1秒确保终止

    def get_steam_process(self):
        """获取Steam进程，支持多种可能的进程名"""
        steam_process_names = ['steam.exe', 'steamwebhelper.exe', 'steamservice.exe']
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name']:
                    proc_name = proc.info['name'].lower()
                    if any(steam_name in proc_name for steam_name in steam_process_names):
                        return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return None


# 主窗口
class ShutdownApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("定时/Steam下载完成自动关机工具")
        self.resize(650, 550)  # 设置初始窗口大小
        self.thread = None

        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Microsoft YaHei', Arial, sans-serif;
            }
            QRadioButton {
                font-size: 14px;
                padding: 8px;
                color: #333;
            }
            QRadioButton:checked {
                color: #2196F3;
                font-weight: bold;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2196F3;
            }
            QPushButton {
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton#start {
                background-color: #4CAF50;
            }
            QPushButton#start:hover {
                background-color: #45a049;
            }
            QPushButton#cancel {
                background-color: #f44336;
            }
            QPushButton#cancel:hover {
                background-color: #da190b;
            }
            QLabel {
                font-size: 13px;
                color: #666;
                padding: 5px;
            }
        """)

        # 可选：设置窗口最小尺寸，防止过小
        self.setMinimumSize(500, 350)

        # 控件
        self.radio_timer = QRadioButton("⏰ 定时关机")
        self.radio_steam = QRadioButton("🎮 Steam下载完成后关机")
        self.radio_timer.setChecked(True)

        self.input_minutes = QLineEdit()
        self.input_minutes.setPlaceholderText("输入分钟数（如：10）")

        self.start_btn = QPushButton("开始监控")
        self.start_btn.setObjectName("start")
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancel")
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_label.setMinimumHeight(40)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.countdown_label = QLabel("")
        self.countdown_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #FF6B6B;
                background-color: #ffe6e6;
                border: 2px solid #FF6B6B;
                border: 1px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                text-align: center;
            }
        """)
        self.countdown_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.countdown_label.setMinimumHeight(40)
        self.countdown_label.setAlignment(Qt.AlignCenter)

        # 布局
        vbox = QVBoxLayout()
        vbox.setSpacing(15)  # 增加控件间距
        vbox.setContentsMargins(20, 20, 20, 20)  # 增加边距
        
        # 添加标题
        title_label = QLabel('<a href="https://space.bilibili.com/23839618/favlist" style="color:#2196F3;text-decoration:none;">🔧 by Executi0n</a>')
        title_label.setOpenExternalLinks(True)
        title_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2196F3;
                text-align: center;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        vbox.addWidget(title_label)
        
        vbox.addWidget(self.radio_timer)
        vbox.addWidget(self.input_minutes)
        vbox.addWidget(self.radio_steam)

        hbox = QHBoxLayout()
        hbox.addWidget(self.start_btn)
        hbox.addWidget(self.cancel_btn)
        hbox.setSpacing(15)

        vbox.addLayout(hbox)
        vbox.addWidget(self.status_label)
        vbox.addWidget(self.countdown_label)  # 添加倒计时标签到布局
        self.setLayout(vbox)

        # 信号绑定
        self.start_btn.clicked.connect(self.start_shutdown)
        self.cancel_btn.clicked.connect(self.cancel_shutdown)

    def start_shutdown(self):
        if self.thread and self.thread.isRunning():
            QMessageBox.warning(self, "提示", "已有任务运行中")
            return

        if self.radio_timer.isChecked():
            try:
                minutes = int(self.input_minutes.text())
                if minutes <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "输入错误", "请输入有效的分钟数")
                return
            self.thread = ShutdownThread(mode="timer", minutes=minutes)

        elif self.radio_steam.isChecked():
            self.thread = ShutdownThread(mode="steam")

        if self.thread:  # 添加检查确保thread不为None
            self.thread.update_status.connect(self.status_label.setText)
            self.thread.update_countdown.connect(self.countdown_label.setText)  # 连接倒计时信号
            self.thread.trigger_shutdown.connect(self.execute_shutdown)
            self.thread.start()

    def cancel_shutdown(self):
        if self.thread:
            self.thread.stop()
            self.status_label.setText("已取消关机任务")
            self.countdown_label.setText("")  # 清空倒计时显示

    def execute_shutdown(self):
        self.status_label.setText("正在关机...")
        self.countdown_label.setText("正在关机...")
        os.system("shutdown -s -t 0")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ShutdownApp()
    win.show()
    sys.exit(app.exec_())
