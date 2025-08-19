import os
import re
import time
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlparse
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    import pdfkit

    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager

    USE_WEBDRIVER_MANAGER = True
except ImportError:
    USE_WEBDRIVER_MANAGER = False


class Config:
    CHROMEDRIVER_PATH = {
        'windows': r'C:\chromedriver\chromedriver.exe',
        'linux': '/usr/local/bin/chromedriver',
        'darwin': '/usr/local/bin/chromedriver'
    }
    START_URLS = [
        "https://mp.weixin.qq.com/s/dlJztvIcQ76bvDfPftvbOw",
    ]
    DOWNLOAD_FOLDER = "WeChat_Articles"
    SAVE_AS_PDF = False
    MAX_ARTICLES = 10
    WAIT_TIME = 3
    HEADLESS_MODE = False
    TIMEOUT = 30


def get_system_type():
    import platform
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'darwin'
    else:
        return 'linux'


def find_chromedriver():
    system_type = get_system_type()
    if USE_WEBDRIVER_MANAGER:
        try:
            driver_path = ChromeDriverManager().install()
            return driver_path
        except Exception as e:
            pass
    manual_path = Config.CHROMEDRIVER_PATH.get(system_type)
    if manual_path and os.path.exists(manual_path):
        return manual_path
    chromedriver_names = ['chromedriver', 'chromedriver.exe']
    for name in chromedriver_names:
        for path in os.environ.get('PATH', '').split(os.pathsep):
            full_path = os.path.join(path, name)
            if os.path.exists(full_path):
                return full_path
    for name in chromedriver_names:
        if os.path.exists(name):
            return os.path.abspath(name)
    return None


def setup_driver(headless=False):
    driver_path = find_chromedriver()
    if not driver_path:
        return None
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    try:
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(Config.TIMEOUT)
        driver.implicitly_wait(10)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        return None


def clean_filename(title):
    if not title:
        return "未命名文章"
    title = title.strip()
    rstr = r"[\/\\\:\*\?\"\<\>\|]"
    new_title = re.sub(rstr, "_", title)
    new_title = re.sub(r'\s+', ' ', new_title)
    return new_title[:100]


def extract_wechat_links(soup):
    links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href and 'mp.weixin.qq.com/s' in href:
            clean_link = clean_wechat_url(href)
            if clean_link:
                links.add(clean_link)
    return list(links)


def clean_wechat_url(url):
    try:
        parsed = urlparse(url)
        if 'mp.weixin.qq.com' not in parsed.netloc:
            return None
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            params = {}
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key in ['__biz', 'mid', 'idx', 'sn']:
                        params[key] = value
            if params:
                param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                return f"{base_url}?{param_str}"
        return base_url
    except Exception:
        return None


def wait_for_page_load(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except Exception as e:
        return False


def process_article(driver, url, download_folder, log_callback=None):
    if log_callback:
        log_callback(f"处理文章: {url}")
    try:
        driver.get(url)
        if not wait_for_page_load(driver, timeout=15):
            if log_callback:
                log_callback("页面加载可能不完整，继续处理...")
        time.sleep(Config.WAIT_TIME)
        if log_callback:
            log_callback("加载完整内容...")
        try:
            total_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(1, 4):
                scroll_to = int(total_height * i / 3)
                driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                time.sleep(1)
        except Exception as e:
            if log_callback:
                log_callback(f"滚动时出错: {e}")
        html = driver.page_source
        if not html or len(html) < 1000:
            if log_callback:
                log_callback("页面内容为空或过少")
            return []
        soup = BeautifulSoup(html, 'html.parser')
        title = "未命名文章"
        title_selectors = [
            {'id': 'activity-name'},
            {'class_': 'rich_media_title'},
            {'class_': 'rich_media_title_text'},
        ]
        for selector in title_selectors:
            title_tag = soup.find(['h1', 'h2', 'div'], selector)
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title:
                    break
        if log_callback:
            log_callback(f"标题: {title}")
        content_div = None
        content_selectors = [
            {'id': 'js_content'},
            {'class_': 'rich_media_content'},
            {'class_': 'rich_media_content_text'},
        ]
        for selector in content_selectors:
            content_div = soup.find('div', selector)
            if content_div and content_div.get_text(strip=True):
                break
        if not content_div or not content_div.get_text(strip=True):
            if log_callback:
                log_callback("未找到有效的正文内容")
            return []
        for img in content_div.find_all('img'):
            if img.get('data-src'):
                img['src'] = img['data-src']
            elif img.get('data-original'):
                img['src'] = img['data-original']
        safe_filename = clean_filename(title)
        html_path = Path(download_folder) / f"{safe_filename}.html"
        counter = 1
        while html_path.exists():
            html_path = Path(download_folder) / f"{safe_filename}_{counter}.html"
            counter += 1
        article_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ 
                    font-family: 'Microsoft YaHei', 'PingFang SC', 'Hiragino Sans GB', sans-serif; 
                    line-height: 1.8; 
                    max-width: 800px; 
                    margin: 40px auto; 
                    padding: 20px; 
                    color: #333;
                    background-color: #fff;
                }}
                h1 {{ 
                    text-align: center; 
                    margin-bottom: 20px;
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                img {{ 
                    max-width: 100%; 
                    height: auto; 
                    display: block; 
                    margin: 20px auto; 
                    border-radius: 5px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                p {{ margin-bottom: 15px; }}
                .article-meta {{
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 14px;
                    margin-bottom: 30px;
                }}
                .source-url {{
                    word-break: break-all;
                    font-size: 12px;
                    color: #95a5a6;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="article-meta">爬取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            <div class="content">
                {str(content_div)}
            </div>
            <div class="source-url">原文链接: {url}</div>
        </body>
        </html>
        """
        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(article_html)
            if log_callback:
                log_callback(f"已保存: {html_path.name}")
        except Exception as e:
            if log_callback:
                log_callback(f"保存失败: {e}")
            return []
        new_links = extract_wechat_links(soup)
        if log_callback:
            log_callback(f"找到 {len(new_links)} 个新链接")
        return new_links
    except Exception as e:
        if log_callback:
            log_callback(f"处理失败: {e}")
        return []


def validate_start_urls(urls):
    valid_urls = []
    for url in urls:
        if url and 'mp.weixin.qq.com' in url and 'your_article_link' not in url:
            valid_urls.append(url)
    return valid_urls


class CrawlerThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(int, int, str)

    def __init__(self, urls, folder, max_articles, wait_time, headless):
        super().__init__()
        self.urls = urls
        self.folder = folder
        self.max_articles = max_articles
        self.wait_time = wait_time
        self.headless = headless
        self.is_running = True

    def run(self):
        start_urls = validate_start_urls(self.urls)
        if not start_urls:
            self.log_signal.emit("没有有效的微信文章链接")
            self.finished_signal.emit(0, 0, self.folder)
            return

        driver = setup_driver(self.headless)
        if not driver:
            self.log_signal.emit("WebDriver 初始化失败")
            self.finished_signal.emit(0, 0, self.folder)
            return

        try:
            Path(self.folder).mkdir(parents=True, exist_ok=True)
            self.log_signal.emit(f"保存目录: {os.path.abspath(self.folder)}")

            urls_to_visit = deque(start_urls)
            visited_urls = set()
            successful_downloads = 0

            self.log_signal.emit(f"开始爬取，最多 {self.max_articles} 篇文章")
            self.log_signal.emit(f"请求间隔: {self.wait_time} 秒")

            while urls_to_visit and len(visited_urls) < self.max_articles and self.is_running:
                current_url = urls_to_visit.popleft()
                clean_url = clean_wechat_url(current_url)
                if not clean_url:
                    continue
                if clean_url in visited_urls:
                    continue

                visited_urls.add(clean_url)
                self.progress_signal.emit(len(visited_urls), self.max_articles)

                Config.WAIT_TIME = self.wait_time
                new_links = process_article(driver, clean_url, self.folder, self.log_signal.emit)

                if new_links is not None:
                    successful_downloads += 1
                    for link in new_links:
                        clean_link = clean_wechat_url(link)
                        if clean_link and clean_link not in visited_urls:
                            urls_to_visit.append(clean_link)
                    self.log_signal.emit(f"队列剩余: {len(urls_to_visit)} 个链接")

                if len(visited_urls) < self.max_articles and urls_to_visit and self.is_running:
                    self.log_signal.emit(f"等待 {self.wait_time} 秒...")
                    time.sleep(self.wait_time)

            self.log_signal.emit("爬取完成！")
            self.log_signal.emit(f"总访问链接: {len(visited_urls)}")
            self.log_signal.emit(f"成功下载: {successful_downloads}")
            self.finished_signal.emit(len(visited_urls), successful_downloads, os.path.abspath(self.folder))

        except Exception as e:
            self.log_signal.emit(f"程序异常: {e}")
            import traceback
            self.log_signal.emit(traceback.format_exc())
        finally:
            try:
                driver.quit()
                self.log_signal.emit("浏览器已关闭")
            except:
                pass

    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.crawler_thread = None

    def init_ui(self):
        self.setWindowTitle("微信公众号文章爬虫")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        urls_group = QGroupBox("文章链接")
        urls_layout = QVBoxLayout(urls_group)

        self.urls_text = QTextEdit()
        self.urls_text.setPlaceholderText("输入微信文章链接，每行一个\n例如：https://mp.weixin.qq.com/s/xxxxxxxxx")
        self.urls_text.setMaximumHeight(120)
        self.urls_text.setText("https://mp.weixin.qq.com/s/dlJztvIcQ76bvDfPftvbOw")
        urls_layout.addWidget(self.urls_text)

        settings_group = QGroupBox("设置")
        settings_layout = QGridLayout(settings_group)

        settings_layout.addWidget(QLabel("保存目录:"), 0, 0)
        self.folder_line = QLineEdit("WeChat_Articles")
        settings_layout.addWidget(self.folder_line, 0, 1)
        self.folder_btn = QPushButton("选择")
        self.folder_btn.clicked.connect(self.select_folder)
        settings_layout.addWidget(self.folder_btn, 0, 2)

        settings_layout.addWidget(QLabel("最大文章数:"), 1, 0)
        self.max_articles_spin = QSpinBox()
        self.max_articles_spin.setRange(1, 1000)
        self.max_articles_spin.setValue(10)
        settings_layout.addWidget(self.max_articles_spin, 1, 1)

        settings_layout.addWidget(QLabel("等待时间(秒):"), 2, 0)
        self.wait_time_spin = QSpinBox()
        self.wait_time_spin.setRange(1, 60)
        self.wait_time_spin.setValue(3)
        settings_layout.addWidget(self.wait_time_spin, 2, 1)

        self.headless_check = QCheckBox("无头模式(不显示浏览器)")
        settings_layout.addWidget(self.headless_check, 3, 0, 1, 3)

        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始爬取")
        self.start_btn.clicked.connect(self.start_crawl)
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_crawl)
        self.stop_btn.setEnabled(False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()

        self.progress_label = QLabel("进度: 0/0")
        control_layout.addWidget(self.progress_label)

        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)

        layout.addWidget(urls_group)
        layout.addWidget(settings_group)
        layout.addLayout(control_layout)
        layout.addWidget(log_group)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if folder:
            self.folder_line.setText(folder)

    def start_crawl(self):
        urls = [url.strip() for url in self.urls_text.toPlainText().split('\n') if url.strip()]
        if not urls:
            QMessageBox.warning(self, "警告", "请输入至少一个微信文章链接")
            return

        folder = self.folder_line.text().strip()
        if not folder:
            QMessageBox.warning(self, "警告", "请设置保存目录")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_text.clear()

        self.crawler_thread = CrawlerThread(
            urls,
            folder,
            self.max_articles_spin.value(),
            self.wait_time_spin.value(),
            self.headless_check.isChecked()
        )
        self.crawler_thread.log_signal.connect(self.add_log)
        self.crawler_thread.progress_signal.connect(self.update_progress)
        self.crawler_thread.finished_signal.connect(self.crawl_finished)
        self.crawler_thread.start()

    def stop_crawl(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.add_log("正在停止爬取...")

    def add_log(self, text):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {text}")
        self.log_text.ensureCursorVisible()

    def update_progress(self, current, total):
        self.progress_label.setText(f"进度: {current}/{total}")

    def crawl_finished(self, visited, success, folder):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText(f"完成: {visited}/{self.max_articles_spin.value()}")

        QMessageBox.information(
            self,
            "完成",
            f"爬取完成！\n访问链接: {visited}\n成功保存: {success}\n保存位置: {folder}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())