# Auto Shutdown Tool | 自动关机工具

**A PyQt5-based GUI application for automatic system shutdown with timer and Steam download monitoring modes.**  
一个基于PyQt5的图形界面工具，支持定时自动关机和Steam下载完成后自动关机。

---

## Features | 功能特性

- **Timer Shutdown Mode**: Set a countdown timer in minutes to automatically shutdown your computer  
  定时关机模式：设置分钟数倒计时，时间到自动关机

- **Steam Monitor Mode**: Automatically shutdown when Steam downloads complete (detects network and disk activity)  
  Steam监控模式：监控Steam下载状态，下载完成后自动关机

- **Real-time Status Display**: Shows current system activity and countdown timer  
  实时状态显示：显示当前系统活动和倒计时时间

- **Safe Cancellation**: Allows canceling shutdown operation anytime  
  安全取消：随时取消关机任务

- **Multi-threaded**: Non-blocking operation with background monitoring  
  多线程处理：后台监控不阻塞界面

- **Visual Feedback**: Clean, modern UI with real-time updates  
  可视化反馈：简洁现代的界面，实时更新状态

---

## Usage | 使用方法

### Timer Mode | 定时模式:
1. Select "⏰ 定时关机" radio button  
   选择"⏰ 定时关机"单选按钮
2. Enter minutes in the input field (e.g., 30)  
   在输入框中输入分钟数（例如：30）
3. Click "开始监控"  
   点击"开始监控"按钮

### Steam Mode | Steam模式:
1. Ensure Steam is running and downloading  
   确保Steam正在运行且正在下载
2. Select "🎮 Steam下载完成后关机" radio button  
   选择"🎮 Steam下载完成后关机"单选按钮
3. Click "开始监控"  
   点击"开始监控"按钮
4. The tool will monitor network and disk activity every 5 seconds  
   工具每5秒监控一次网络和磁盘活动
5. Automatically shutdown 2 minutes after activity stops  
   活动停止2分钟后自动关机

### Cancel Operation | 取消操作:
- Click "取消" button at any time to abort shutdown  
  任何时候点击"取消"按钮中止关机

---

## System Requirements | 系统要求

- Windows operating system  
  Windows操作系统
- Python 3.x  
  Python 3.x
- PyQt5 library  
  PyQt5库
- psutil library  
  psutil库
- webbrowser module (standard library)  
  webbrowser模块（标准库）

---

## Technical Details | 技术细节

### Monitored Steam Processes | 监控的Steam进程
- `steam.exe`
- `steamwebhelper.exe`
- `steamservice.exe`

### Activity Thresholds | 活动阈值
- **Network**: Active when download/upload &gt; 100 KB/s  
  网络：下载/上传速度大于100 KB/s时视为活跃
- **Disk**: Active when read/write &gt; 1024 KB/s  
  磁盘：读取/写入速度大于1024 KB/s时视为活跃
- **Idle Duration**: 120 seconds of inactivity triggers shutdown  
  空闲时长：120秒无活动后触发关机

### Shutdown Command | 关机命令
Uses Windows native shutdown command: `shutdown -s -t 0`  
使用Windows原生关机命令：`shutdown -s -t 0`

---

## Important Notes | 重要提示

⚠️ **Run as Administrator**: May require administrator privileges for proper operation  
⚠️ 以管理员身份运行：可能需要管理员权限才能正常工作

⚠️ **Save Your Work**: Ensure all important work is saved before starting  
⚠️ 保存工作：启动前请确保所有重要工作已保存

⚠️ **Steam Process Detection**: If Steam is not detected, the tool will show a warning message  
⚠️ Steam进程检测：如果未检测到Steam进程，工具会显示警告信息

⚠️ **Network Interface Monitoring**: Monitors system-wide network activity, not Steam-specific traffic  
⚠️ 网络接口监控：监控系统整体网络活动，而非Steam特定流量

⚠️ **Manual Cancellation**: Always use the "取消" button to stop monitoring; closing the window may not terminate background threads properly  
⚠️ 手动取消：请使用"取消"按钮停止监控；直接关闭窗口可能无法正确终止后台线程

---

## Author | 作者

**Executi0n**  
Bilibili: [https://space.bilibili.com/23839618](https://space.bilibili.com/23839618)

---

## License | 许可证

This tool is provided as-is for personal use. Use at your own risk.  
本工具按原样提供，仅限个人使用。使用风险自负。