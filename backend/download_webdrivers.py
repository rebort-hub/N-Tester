"""
预下载所有WebDriver驱动程序

【重要说明】
webdriver-manager 会自动管理驱动下载，无需手动预下载。
- 首次执行测试时会自动下载驱动（30-60秒）
- 后续执行使用缓存（3-5秒）
- 驱动缓存在 ~/.wdm/ 目录

【何时使用此脚本】
✓ 生产环境部署时（避免首次执行慢）
✓ Docker 镜像构建时（在构建阶段完成下载）
✓ 离线环境准备时（提前下载好驱动）
✗ 开发环境（不需要，自动下载即可）

【用法】
开发环境：
  .venv\Scripts\python.exe download_webdrivers.py

生产环境（Dockerfile）：
  RUN python download_webdrivers.py

生产环境（部署脚本）：
  python download_webdrivers.py
"""
import os
import sys
import time

# 设置环境变量
os.environ['WDM_LOG'] = '1'  # 启用详细日志
os.environ['WDM_PRINT_FIRST_LINE'] = 'True'  # 打印首行信息

def download_chrome_driver():
    """下载 ChromeDriver"""
    print("\n" + "="*80)
    print("正在下载 ChromeDriver...")
    print("="*80)
    
    try:
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        start_time = time.time()
        
        # 显示下载进度
        print("\n提示：首次下载可能需要几分钟，请耐心等待...")
        print("下载地址：https://chromedriver.storage.googleapis.com/")
        
        driver_path = ChromeDriverManager().install()
        
        elapsed = time.time() - start_time
        print(f"\n✓ ChromeDriver 下载成功！(耗时: {elapsed:.1f}秒)")
        print(f"  安装路径: {driver_path}")
        
        # 验证驱动
        print("\n验证驱动...")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        version = driver.capabilities['browserVersion']
        driver.quit()
        
        print(f"✓ 驱动验证成功！Chrome 版本: {version}")
        return True
        
    except Exception as e:
        print(f"\n✗ ChromeDriver 下载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def download_firefox_driver():
    """下载 GeckoDriver (Firefox)"""
    print("\n" + "="*80)
    print("正在下载 GeckoDriver (Firefox)...")
    print("="*80)
    
    try:
        from selenium.webdriver.firefox.service import Service
        from webdriver_manager.firefox import GeckoDriverManager
        
        start_time = time.time()
        
        print("\n提示：首次下载可能需要几分钟，请耐心等待...")
        print("下载地址：https://github.com/mozilla/geckodriver/releases/")
        
        driver_path = GeckoDriverManager().install()
        
        elapsed = time.time() - start_time
        print(f"\n✓ GeckoDriver 下载成功！(耗时: {elapsed:.1f}秒)")
        print(f"  安装路径: {driver_path}")
        return True
        
    except Exception as e:
        print(f"\n✗ GeckoDriver 下载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def download_edge_driver():
    """下载 EdgeDriver"""
    print("\n" + "="*80)
    print("正在下载 EdgeDriver...")
    print("="*80)
    
    try:
        from selenium.webdriver.edge.service import Service
        from webdriver_manager.microsoft import EdgeChromiumDriverManager
        
        start_time = time.time()
        
        print("\n提示：首次下载可能需要几分钟，请耐心等待...")
        print("下载地址：https://msedgedriver.azureedge.net/")
        
        driver_path = EdgeChromiumDriverManager().install()
        
        elapsed = time.time() - start_time
        print(f"\n✓ EdgeDriver 下载成功！(耗时: {elapsed:.1f}秒)")
        print(f"  安装路径: {driver_path}")
        return True
        
    except Exception as e:
        print(f"\n✗ EdgeDriver 下载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def check_browser_installed():
    """检查浏览器是否已安装"""
    print("\n" + "="*80)
    print("检查已安装的浏览器...")
    print("="*80)
    
    browsers = {
        'Chrome': False,
        'Firefox': False,
        'Edge': False
    }
    
    # 检查 Chrome
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
        chrome_path = winreg.QueryValue(key, None)
        winreg.CloseKey(key)
        browsers['Chrome'] = True
        print(f"✓ Chrome 已安装: {chrome_path}")
    except:
        print("✗ Chrome 未安装")
    
    # 检查 Firefox
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe")
        firefox_path = winreg.QueryValue(key, None)
        winreg.CloseKey(key)
        browsers['Firefox'] = True
        print(f"✓ Firefox 已安装: {firefox_path}")
    except:
        print("✗ Firefox 未安装")
    
    # 检查 Edge
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe")
        edge_path = winreg.QueryValue(key, None)
        winreg.CloseKey(key)
        browsers['Edge'] = True
        print(f"✓ Edge 已安装: {edge_path}")
    except:
        print("✗ Edge 未安装")
    
    return browsers


def main():
    """主函数"""
    print("\n" + "="*80)
    print("WebDriver 驱动程序下载工具")
    print("="*80)
    print("\n此工具将预下载所有浏览器的 WebDriver 驱动程序")
    print("首次下载可能需要几分钟时间，请耐心等待...")
    
    # 检查浏览器
    installed_browsers = check_browser_installed()
    
    # 下载驱动
    results = {}
    
    if installed_browsers['Chrome']:
        results['Chrome'] = download_chrome_driver()
    else:
        print("\n⚠️  Chrome 未安装，跳过 ChromeDriver 下载")
        results['Chrome'] = None
    
    if installed_browsers['Firefox']:
        results['Firefox'] = download_firefox_driver()
    else:
        print("\n⚠️  Firefox 未安装，跳过 GeckoDriver 下载")
        results['Firefox'] = None
    
    if installed_browsers['Edge']:
        results['Edge'] = download_edge_driver()
    else:
        print("\n⚠️  Edge 未安装，跳过 EdgeDriver 下载")
        results['Edge'] = None
    
    # 总结
    print("\n" + "="*80)
    print("下载完成！")
    print("="*80)
    
    success_count = sum(1 for v in results.values() if v is True)
    failed_count = sum(1 for v in results.values() if v is False)
    skipped_count = sum(1 for v in results.values() if v is None)
    
    print(f"\n成功: {success_count}个")
    print(f"失败: {failed_count}个")
    print(f"跳过: {skipped_count}个")
    
    if success_count > 0:
        print("\n✓ 驱动程序已缓存，后续测试执行将会更快！")
    
    if failed_count > 0:
        print("\n⚠️  部分驱动下载失败，请检查网络连接或手动下载")
        print("\n手动下载地址：")
        print("  ChromeDriver: https://chromedriver.chromium.org/downloads")
        print("  GeckoDriver: https://github.com/mozilla/geckodriver/releases")
        print("  EdgeDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断下载")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
