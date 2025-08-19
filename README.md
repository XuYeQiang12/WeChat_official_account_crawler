# WeChat_official_account_crawler
<img width="801" height="629" alt="image" src="https://github.com/user-attachments/assets/31ca59cc-f6b1-415e-bfec-94b3db606e97" />

微信公众号爬虫--仅供学习参考

## 微信公众号文章爬虫 - 环境配置说明

### 系统要求
- Python 3.7 或更高版本
- Chrome 浏览器
- 操作系统：Windows, macOS, Linux

### 快速开始

#### 1. 克隆或下载项目文件
确保包含以下文件：  
- wechat_crawler_gui.py (主程序)  
- requirements.txt (依赖列表)

```bash
# 创建虚拟环境
python -m venv wechat_env

# Windows 激活
wechat_env\Scripts\activate

# macOS/Linux 激活  
source wechat_env/bin/activate

# 升级pip
python -m pip install --upgrade pip

# 安装依赖包
pip install -r requirements.txt
```

#### Windows 系统：
查看 Chrome 版本：

1. 打开 Chrome 浏览器
2. 地址栏输入：chrome://version/
3. 记录版本号（如：120.0.6099.109）
<img width="1009" height="340" alt="image" src="https://github.com/user-attachments/assets/eb2459e2-50c4-4a0c-83d3-d878e327b264" />

下载 ChromeDriver：

1. 访问：https://googlechromelabs.github.io/chrome-for-testing/
2. 下载与您 Chrome 版本对应的 ChromeDriver
3. 创建目录：C:\chromedriver\
4. 将下载包含 chromedriver.exe 放入该目录

#### Linux 系统
```bash
# 下载并安装
wget https://chromedriver.storage.googleapis.com/版本号/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```
