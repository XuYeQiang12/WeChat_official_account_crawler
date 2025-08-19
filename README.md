项目介绍
这是一个基于 PyQt5 界面的微信公众号文章爬虫工具，可以批量下载微信公众号文章并保存为 HTML 格式。

系统要求
Python: 3.7 或更高版本
浏览器: Chrome 浏览器
操作系统: Windows, macOS, Linux
项目文件
确保包含以下文件：

wechat_crawler_gui.py (主程序)
requirements.txt (依赖列表)
快速开始
1. 创建虚拟环境
bash
# 创建虚拟环境
python -m venv wechat_env
2. 激活虚拟环境
Windows:

bash
wechat_env\Scripts\activate
macOS/Linux:

bash
source wechat_env/bin/activate
3. 安装依赖
bash
# 升级pip
python -m pip install --upgrade pip

# 安装依赖包
pip install -r requirements.txt

# 如果网络较慢，使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
ChromeDriver 配置
Windows 系统
查看 Chrome 版本：

打开 Chrome 浏览器
地址栏输入：chrome://version/
记录版本号（如：120.0.6099.109）
下载 ChromeDriver：

访问：https://googlechromelabs.github.io/chrome-for-testing/
或：https://chromedriver.chromium.org/downloads
下载与您 Chrome 版本对应的 ChromeDriver
安装配置：

创建目录：C:\chromedriver\
将下载的 chromedriver.exe 放入该目录
Linux 系统
bash
# 下载并安装 (替换版本号为实际版本)
wget https://chromedriver.storage.googleapis.com/[版本号]/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# 验证安装
chromedriver --version
macOS 系统
bash
# 使用 Homebrew 安装
brew install chromedriver

# 或手动下载安装
wget https://chromedriver.storage.googleapis.com/[版本号]/chromedriver_mac64.zip
unzip chromedriver_mac64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
运行程序
bash
python wechat_crawler_gui.py
使用说明
启动程序 - 双击运行或命令行启动
输入链接 - 在"文章链接"区域输入微信文章URL（每行一个）
配置设置：
设置保存目录
调整最大文章数
设置请求间隔时间
选择是否使用无头模式
开始爬取 - 点击"开始爬取"按钮
查看结果 - 文章将保存为HTML格式到指定目录
可能遇到的问题
Linux 系统额外依赖
如果在 Linux 上遇到 PyQt5 相关错误：

Ubuntu/Debian:

bash
sudo apt-get update
sudo apt-get install -y python3-pyqt5 libxcb-xinerama0 libxcb-cursor0 libxkbcommon-x11-0
CentOS/RHEL:

bash
sudo yum install -y qt5-qtbase-devel libxcb-devel
验证安装
python
# 在 Python 中运行以下代码验证
from PyQt5.QtWidgets import QApplication
import selenium
from bs4 import BeautifulSoup
print("所有依赖安装成功！")
功能特性
✅ PyQt5 图形界面，操作简单
✅ 支持批量爬取文章
✅ 自动提取文章中的相关链接
✅ 保存为格式化的 HTML 文件
✅ 实时日志显示
✅ 支持自定义爬取参数
✅ 自动处理 ChromeDriver
注意事项
⚠️ 重要提示：

本项目仅供学习和研究使用
请遵守微信公众平台的使用条款和robots.txt
建议设置合理的请求间隔，避免对服务器造成压力
不要用于商业用途或大规模数据采集
使用时请承担相应的法律责任
许可证
本项目仅供学习参考，使用时请遵守相关法律法规。
