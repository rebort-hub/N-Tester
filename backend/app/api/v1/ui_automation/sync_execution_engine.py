"""
UI自动化模块 - 同步执行引擎
使用同步 Playwright 避免 Windows asyncio subprocess 问题
"""
import time
import logging
import traceback
from typing import Dict, Any, List
from datetime import datetime
from playwright.sync_api import sync_playwright, Page

logger = logging.getLogger(__name__)


class SyncExecutionEngine:
    """同步执行引擎（使用 sync_playwright）"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def execute_test_case(
        self,
        test_case_data: Dict[str, Any],
        steps_data: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行测试用例"""
        start_time = time.time()
        logs = []
        passed_steps = 0
        failed_steps = 0
        screenshots = []  # 收集截图
        
        try:
            # 获取配置
            browser_type = config.get('browser_type', 'chromium')
            headless = config.get('headless', True)
            channel = config.get('channel', None)
            
            # 启动 Playwright
            with sync_playwright() as p:
                # 选择浏览器
                if browser_type == 'firefox':
                    self.browser = p.firefox.launch(headless=headless)
                elif browser_type == 'webkit':
                    self.browser = p.webkit.launch(headless=headless)
                else:  # chromium, chrome, edge
                    launch_options = {'headless': headless}
                    if channel:
                        launch_options['channel'] = channel
                    self.browser = p.chromium.launch(**launch_options)
                
                browser_info = f"{browser_type}"
                if channel:
                    browser_info += f" (channel={channel})"
                browser_info += f", headless={headless}"
                logs.append(f"✓ 浏览器启动成功: {browser_info}")
                
                # 创建上下文和页面
                self.context = self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
                self.page = self.context.new_page()
                
                # 导航到 base_url
                base_url = test_case_data.get('base_url')
                if base_url:
                    try:
                        logs.append(f"正在导航到: {base_url}")
                        self.page.goto(base_url, wait_until='networkidle', timeout=30000)
                        time.sleep(2)  # 额外等待确保页面加载完成
                        logs.append(f"✓ 成功导航到: {base_url}")
                        logs.append(f"  - 等待页面加载完成（networkidle + 额外2秒）")
                    except Exception as e:
                        error_msg = f"✗ 导航失败: {str(e)}"
                        logs.append(error_msg)
                        return {
                            'status': 'failed',
                            'total_steps': len(steps_data),
                            'passed_steps': 0,
                            'failed_steps': len(steps_data),
                            'duration': int((time.time() - start_time) * 1000),
                            'logs': '\n'.join(logs),
                            'error_message': error_msg
                        }
                
                # 执行测试步骤
                for step_data in steps_data:
                    step_num = step_data['step_number']
                    action_type = step_data['action_type']
                    description = step_data.get('description', '')
                    
                    logs.append(f"步骤 {step_num}: {description or action_type}")
                    
                    try:
                        step_start = time.time()
                        self._execute_step(step_data, logs)
                        step_duration = time.time() - step_start
                        
                        logs.append(f"  ✓ 执行成功")
                        logs.append(f"    - 执行时间: {step_duration:.2f}秒")
                        passed_steps += 1
                        
                    except Exception as e:
                        step_duration = time.time() - step_start
                        error_msg = str(e)
                        logs.append(f"  ✗ 执行失败")
                        logs.append(f"    - 执行时间: {step_duration:.2f}秒")
                        logs.append(f"    - 错误: {error_msg}")
                        failed_steps += 1
                        
                        # 捕获失败截图
                        try:
                            import base64
                            screenshot_bytes = self.page.screenshot()
                            screenshot_base64 = f"data:image/png;base64,{base64.b64encode(screenshot_bytes).decode()}"
                            screenshots.append({
                                'step_number': step_num,
                                'step_description': description or action_type,
                                'error_message': error_msg,
                                'screenshot': screenshot_base64,
                                'timestamp': datetime.now().isoformat()
                            })
                            logs.append(f"    - 已捕获失败截图")
                        except Exception as screenshot_error:
                            logs.append(f"    - 截图失败: {str(screenshot_error)}")
                        
                        # 失败后停止执行
                        logs.append(f"  ✗ 步骤失败，停止执行")
                        break
                
                # 关闭浏览器
                self.browser.close()
                logs.append(f"✓ 浏览器已关闭")
            
            duration = int((time.time() - start_time) * 1000)
            status = 'success' if failed_steps == 0 else 'failed'
            
            return {
                'status': status,
                'total_steps': len(steps_data),
                'passed_steps': passed_steps,
                'failed_steps': failed_steps,
                'duration': duration,
                'logs': '\n'.join(logs),
                'screenshots': screenshots,  # 返回截图列表
                'error_message': None if status == 'success' else f"{failed_steps} 个步骤失败"
            }
            
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            error_detail = f"执行异常: {str(e)}\n\n详细错误:\n{traceback.format_exc()}"
            logs.append(f"\n✗ 执行异常:\n{error_detail}")
            
            # 尝试捕获异常时的截图
            try:
                if self.page:
                    import base64
                    screenshot_bytes = self.page.screenshot()
                    screenshot_base64 = f"data:image/png;base64,{base64.b64encode(screenshot_bytes).decode()}"
                    screenshots.append({
                        'step_number': 0,
                        'step_description': '执行异常',
                        'error_message': str(e),
                        'screenshot': screenshot_base64,
                        'timestamp': datetime.now().isoformat()
                    })
            except:
                pass
            
            return {
                'status': 'failed',
                'total_steps': len(steps_data),
                'passed_steps': passed_steps,
                'failed_steps': failed_steps or len(steps_data),
                'duration': duration,
                'logs': '\n'.join(logs),
                'screenshots': screenshots,  # 返回截图列表
                'error_message': str(e)
            }
    
    def _execute_step(self, step_data: Dict[str, Any], logs: List[str]):
        """执行单个步骤"""
        action_type = step_data['action_type']
        action_value = step_data.get('action_value')
        element_data = step_data.get('element')
        
        # 等待操作
        if action_type == 'wait':
            wait_time = int(action_value) if action_value else 1000
            time.sleep(wait_time / 1000)
            logs.append(f"    - 等待 {wait_time}ms")
            return
        
        # 需要元素的操作
        if not element_data:
            raise Exception("未指定元素")
        
        # 构建定位器
        locator_strategy = element_data.get('locator_strategy', 'css').lower()
        locator_value = element_data.get('locator_value', '')
        element_name = element_data.get('name', '未知元素')
        
        if not locator_value:
            raise Exception("元素定位器为空")
        
        # 根据定位策略构造 Playwright 选择器
        if locator_strategy in ['css', 'css selector']:
            selector = locator_value
        elif locator_strategy == 'xpath':
            selector = f'xpath={locator_value}'
        elif locator_strategy == 'id':
            selector = f'#{locator_value}'
        elif locator_strategy == 'name':
            selector = f'[name="{locator_value}"]'
        elif locator_strategy == 'text':
            selector = f'text={locator_value}'
        elif locator_strategy == 'placeholder':
            selector = f'[placeholder="{locator_value}"]'
        elif locator_strategy == 'role':
            selector = f'role={locator_value}'
        elif locator_strategy == 'label':
            selector = f'label={locator_value}'
        elif locator_strategy == 'title':
            selector = f'[title="{locator_value}"]'
        elif locator_strategy == 'test-id':
            selector = f'[data-testid="{locator_value}"]'
        else:
            selector = locator_value
        
        # 获取超时时间
        wait_timeout = element_data.get('wait_timeout', 5.0)
        if isinstance(wait_timeout, (int, float)):
            timeout_ms = int(wait_timeout * 1000)
        else:
            timeout_ms = 5000
        
        # 执行操作
        if action_type == 'click':
            self.page.click(selector, timeout=timeout_ms)
            logs.append(f"    ✓ 点击元素 '{element_name}' 成功")
            logs.append(f"      - 定位器: {selector}")
            logs.append(f"      - 超时设置: {wait_timeout}秒")
            
        elif action_type == 'fill':
            if not action_value:
                raise Exception("输入值为空")
            self.page.fill(selector, action_value, timeout=timeout_ms)
            logs.append(f"    ✓ 输入文本 '{action_value}' 成功")
            logs.append(f"      - 元素: '{element_name}'")
            logs.append(f"      - 定位器: {selector}")
            
        elif action_type == 'getText':
            text = self.page.text_content(selector, timeout=timeout_ms)
            logs.append(f"    ✓ 获取文本成功: '{text}'")
            logs.append(f"      - 元素: '{element_name}'")
            
        elif action_type == 'hover':
            self.page.hover(selector, timeout=timeout_ms)
            logs.append(f"    ✓ 悬停元素 '{element_name}' 成功")
            
        elif action_type == 'scroll':
            self.page.locator(selector).scroll_into_view_if_needed(timeout=timeout_ms)
            logs.append(f"    ✓ 滚动到元素 '{element_name}' 成功")
            
        elif action_type == 'waitFor':
            self.page.wait_for_selector(selector, timeout=timeout_ms)
            logs.append(f"    ✓ 等待元素 '{element_name}' 出现成功")
            
        elif action_type == 'screenshot':
            screenshot_path = f"screenshot_{int(time.time())}.png"
            self.page.screenshot(path=screenshot_path)
            logs.append(f"    ✓ 截图成功: {screenshot_path}")
            
        elif action_type == 'assert':
            assertion_type = step_data.get('assertion_type')
            assertion_value = step_data.get('assertion_value')
            
            if assertion_type == 'text':
                actual_text = self.page.text_content(selector, timeout=timeout_ms)
                if actual_text != assertion_value:
                    raise Exception(f"断言失败: 期望 '{assertion_value}', 实际 '{actual_text}'")
                logs.append(f"    ✓ 文本断言成功: '{assertion_value}'")
            elif assertion_type == 'visible':
                is_visible = self.page.is_visible(selector, timeout=timeout_ms)
                if not is_visible:
                    raise Exception(f"断言失败: 元素不可见")
                logs.append(f"    ✓ 可见性断言成功")
            else:
                raise Exception(f"不支持的断言类型: {assertion_type}")
        
        else:
            raise Exception(f"不支持的操作类型: {action_type}")
