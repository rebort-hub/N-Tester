"""
Selenium 执行引擎包装器
"""
import time
import logging
import traceback
from typing import Dict, Any, List
from datetime import datetime
from .selenium_engine import SeleniumTestEngine

logger = logging.getLogger(__name__)


class SeleniumExecutionEngine:
    """Selenium 执行引擎包装器"""
    
    def __init__(self, execution_id=None):
        self.engine = None
        self.execution_id = execution_id
        
    def _is_stopped(self):
        """检查执行是否被停止"""
        if not self.execution_id:
            return False
        
        from .execution_engine import ExecutionManager
        engine = ExecutionManager._instances.get(self.execution_id)
        return engine.is_stopped if engine else False
    
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
            browser_type = config.get('browser_type', 'chrome')
            headless = config.get('headless', True)
            
            # 检查浏览器是否可用
            is_available, error_msg = SeleniumTestEngine.check_browser_available(browser_type)
            if not is_available:
                return {
                    'status': 'failed',
                    'total_steps': len(steps_data),
                    'passed_steps': 0,
                    'failed_steps': len(steps_data),
                    'duration': int((time.time() - start_time) * 1000),
                    'logs': f"✗ 浏览器不可用: {error_msg}",
                    'screenshots': [],  # 空截图列表
                    'error_message': error_msg
                }
            
            # 创建引擎实例
            self.engine = SeleniumTestEngine(browser_type=browser_type, headless=headless)
            
            # 启动浏览器
            self.engine.start()
            
            browser_info = f"{browser_type}, headless={headless}"
            logs.append(f"✓ 浏览器启动成功: {browser_info}")
            
            # 导航到 base_url
            base_url = test_case_data.get('base_url')
            if base_url:
                try:
                    logs.append(f"正在导航到: {base_url}")
                    success, nav_log = self.engine.navigate(base_url)
                    logs.append(nav_log)
                    
                    if not success:
                        return {
                            'status': 'failed',
                            'total_steps': len(steps_data),
                            'passed_steps': 0,
                            'failed_steps': len(steps_data),
                            'duration': int((time.time() - start_time) * 1000),
                            'logs': '\n'.join(logs),
                            'screenshots': [],  # 空截图列表
                            'error_message': '导航失败'
                        }
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
                        'screenshots': [],  # 空截图列表
                        'error_message': error_msg
                    }
            
            # 执行测试步骤
            for step_data in steps_data:
                # 检查是否被停止
                if self._is_stopped():
                    logs.append("⚠ 执行已被用户停止")
                    break
                    
                step_num = step_data['step_number']
                action_type = step_data['action_type']
                description = step_data.get('description', '')
                
                logs.append(f"\n步骤 {step_num}: {description or action_type}")
                
                try:
                    step_start = time.time()
                    
                    # 创建步骤对象（模拟）
                    class StepObject:
                        def __init__(self, data):
                            self.action_type = data['action_type']
                            self.input_value = data.get('action_value')
                            self.assert_type = data.get('assertion_type')
                            self.assert_value = data.get('assertion_value')
                            self.wait_time = data.get('element', {}).get('wait_timeout', 5.0) * 1000 if data.get('element') else 5000
                    
                    step = StepObject(step_data)
                    
                    # 准备元素数据
                    element_data = {}
                    if step_data.get('element'):
                        elem = step_data['element']
                        element_data = {
                            'locator_strategy': elem.get('locator_strategy', 'css'),
                            'locator_value': elem.get('locator_value', ''),
                            'name': elem.get('name', '未知元素'),
                            'wait_timeout': elem.get('wait_timeout', 5.0),
                            'force_action': elem.get('force_action', False)
                        }
                    
                    # 执行步骤
                    success, step_log, screenshot = self.engine.execute_step(step, element_data)
                    step_duration = time.time() - step_start
                    
                    logs.append(step_log)
                    logs.append(f"  - 执行时间: {step_duration:.2f}秒")
                    
                    if success:
                        passed_steps += 1
                    else:
                        failed_steps += 1
                        
                        # 捕获失败截图
                        if screenshot:
                            screenshots.append({
                                'step_number': step_num,
                                'step_description': description or action_type,
                                'error_message': step_log,
                                'screenshot': screenshot,
                                'timestamp': datetime.now().isoformat()
                            })
                            logs.append(f"  - 已捕获失败截图")
                        
                        logs.append(f"  ✗ 步骤失败，停止执行")
                        break
                        
                except Exception as e:
                    step_duration = time.time() - step_start
                    error_msg = str(e)
                    logs.append(f"  ✗ 执行失败")
                    logs.append(f"  - 执行时间: {step_duration:.2f}秒")
                    logs.append(f"  - 错误: {error_msg}")
                    failed_steps += 1
                    
                    # 捕获失败截图
                    try:
                        if self.engine and self.engine.driver:
                            import base64
                            screenshot_bytes = self.engine.driver.get_screenshot_as_png()
                            screenshot_base64 = f"data:image/png;base64,{base64.b64encode(screenshot_bytes).decode()}"
                            screenshots.append({
                                'step_number': step_num,
                                'step_description': description or action_type,
                                'error_message': error_msg,
                                'screenshot': screenshot_base64,
                                'timestamp': datetime.now().isoformat()
                            })
                            logs.append(f"  - 已捕获失败截图")
                    except Exception as screenshot_error:
                        logs.append(f"  - 截图失败: {str(screenshot_error)}")
                    
                    logs.append(f"  ✗ 步骤失败，停止执行")
                    break
            
            # 关闭浏览器
            if self.engine:
                self.engine.stop()
                logs.append(f"\n✓ 浏览器已关闭")
            
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
                if self.engine and self.engine.driver:
                    import base64
                    screenshot_bytes = self.engine.driver.get_screenshot_as_png()
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
            
            # 确保关闭浏览器
            if self.engine:
                try:
                    self.engine.stop()
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
