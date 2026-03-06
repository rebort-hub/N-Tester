"""
UI自动化模块 - 执行引擎
"""
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import traceback

from .playwright_engine import PlaywrightTestEngine
from .model import UIElementModel

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """执行引擎基类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.execution_id = None
        self.is_stopped = False
        self.playwright_engine: Optional[PlaywrightTestEngine] = None
    
    async def execute_test_case(
        self,
        test_case: Any,
        steps: List[Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行测试用例"""
        engine_type = config.get('engine_type', 'playwright')
        
        if engine_type == 'playwright':
            return await self._execute_with_playwright(test_case, steps, config)
        elif engine_type == 'selenium':
            return await self._execute_with_selenium(test_case, steps, config)
        else:
            raise ValueError(f"不支持的执行引擎: {engine_type}")
    
    async def _execute_with_playwright(
        self,
        test_case: Any,
        steps: List[Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用Playwright执行测试"""
        start_time = time.time()
        logs = []
        screenshots = []
        passed_steps = 0
        failed_steps = 0
        
        try:
            # 获取配置
            browser_type = config.get('browser_type', 'chromium')
            headless = config.get('headless', True)
            channel = config.get('channel', None)  # 新增：浏览器渠道
            
            # 创建Playwright引擎
            self.playwright_engine = PlaywrightTestEngine(
                browser_type=browser_type,
                headless=headless,
                channel=channel,
                stop_check_func=lambda: self.is_stopped
            )
            
            # 启动浏览器
            await self.playwright_engine.start()
            browser_info = f"{browser_type}"
            if channel:
                browser_info += f" (channel={channel})"
            browser_info += f", headless={headless}"
            logs.append(f"✓ 浏览器启动成功: {browser_info}")
            
            # 获取 UI 项目的 base_url
            base_url = await self._get_project_base_url(test_case.ui_project_id)
            if base_url:
                success, log = await self.playwright_engine.navigate(base_url)
                logs.append(log)
                if not success:
                    raise Exception(f"导航失败: {base_url}")
            
            # 执行每个步骤
            for step in steps:
                if self.is_stopped:
                    logs.append("⚠ 执行已被用户停止")
                    break
                
                # 获取元素数据
                element_data = await self._get_element_data(step.element_id) if step.element_id else {}
                
                # 执行步骤
                success, log, screenshot = await self.playwright_engine.execute_step(step, element_data)
                
                logs.append(f"\n步骤 {step.step_number}: {step.description or step.action_type}")
                logs.append(log)
                
                if screenshot:
                    screenshots.append({
                        'step_number': step.step_number,
                        'screenshot': screenshot
                    })
                
                if success:
                    passed_steps += 1
                else:
                    failed_steps += 1
                    # 如果步骤失败且不继续执行，则停止
                    if not step.continue_on_failure:
                        logs.append(f"✗ 步骤失败，停止执行")
                        break
            
            # 关闭浏览器
            await self.playwright_engine.stop()
            logs.append("\n✓ 浏览器已关闭")
            
            # 计算执行时长
            duration = int((time.time() - start_time) * 1000)  # 毫秒
            
            # 确定最终状态
            if self.is_stopped:
                status = 'stopped'
            elif failed_steps == 0:
                status = 'success'
            else:
                status = 'failed'
            
            return {
                'status': status,
                'total_steps': len(steps),
                'passed_steps': passed_steps,
                'failed_steps': failed_steps,
                'duration': duration,
                'screenshots': screenshots,
                'logs': '\n'.join(logs),
                'error_message': None if status == 'success' else f'{failed_steps} 个步骤失败'
            }
            
        except Exception as e:
            logger.error(f"Playwright执行异常: {str(e)}", exc_info=True)
            
            # 尝试关闭浏览器
            if self.playwright_engine:
                try:
                    await self.playwright_engine.stop()
                except:
                    pass
            
            duration = int((time.time() - start_time) * 1000)
            
            # 获取详细的错误堆栈
            error_traceback = traceback.format_exc()
            
            return {
                'status': 'failed',
                'total_steps': len(steps),
                'passed_steps': passed_steps,
                'failed_steps': len(steps) - passed_steps,
                'duration': duration,
                'screenshots': screenshots,
                'logs': '\n'.join(logs) + f"\n\n✗ 执行异常: {str(e)}\n\n详细错误:\n{error_traceback}",
                'error_message': str(e)
            }
    
    async def _get_element_data(self, element_id: int) -> Dict[str, Any]:
        """获取元素数据"""
        if not element_id:
            return {}
        
        try:
            query = select(UIElementModel).where(UIElementModel.id == element_id)
            result = await self.db.execute(query)
            element = result.scalar_one_or_none()
            
            if not element:
                return {}
            
            return {
                'id': element.id,
                'name': element.name,
                'locator_strategy': element.locator_strategy,
                'locator_value': element.locator_value,
                'wait_timeout': getattr(element, 'wait_timeout', None) or getattr(element, 'wait_time', 5000) / 1000,  # 转换为秒
                'force_action': getattr(element, 'force_action', False)
            }
        except Exception as e:
            logger.error(f"获取元素数据失败: {str(e)}")
            return {}
    
    async def _get_project_base_url(self, ui_project_id: int) -> str:
        """获取 UI 项目的 base_url"""
        if not ui_project_id:
            return None
        
        try:
            from .model import UIProjectModel
            query = select(UIProjectModel).where(UIProjectModel.id == ui_project_id)
            result = await self.db.execute(query)
            project = result.scalar_one_or_none()
            
            if project and project.base_url:
                return project.base_url
            return None
        except Exception as e:
            logger.error(f"获取项目 base_url 失败: {str(e)}")
            return None
    
    async def _execute_with_selenium(
        self,
        test_case: Any,
        steps: List[Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用 Selenium 执行测试（异步包装）"""
        # 注意：实际的 Selenium 执行在 service.py 的线程中进行
        # 这里仅作为异步接口的占位符，实际不会被调用
        # 真正的执行逻辑在 selenium_engine.py 中
        return {
            'status': 'failed',
            'total_steps': len(steps),
            'passed_steps': 0,
            'failed_steps': len(steps),
            'duration': 0,
            'screenshots': [],
            'logs': 'Selenium 执行应通过 service.py 的线程方式调用',
            'error_message': 'Selenium 执行应通过 service.py 的线程方式调用'
        }
    
    def stop(self):
        """停止执行"""
        self.is_stopped = True
        # 如果Playwright引擎正在运行，立即停止它
        if self.playwright_engine:
            try:
                # 创建一个新的事件循环来运行异步停止方法
                import asyncio
                import threading
                
                def stop_playwright():
                    try:
                        # 在新线程中创建事件循环
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.playwright_engine.stop())
                        loop.close()
                    except Exception as e:
                        logger.error(f"停止Playwright引擎失败: {str(e)}")
                
                # 在新线程中停止Playwright引擎，避免阻塞
                stop_thread = threading.Thread(target=stop_playwright)
                stop_thread.daemon = True
                stop_thread.start()
                
                logger.info(f"执行 {self.execution_id} 已请求停止")
            except Exception as e:
                logger.error(f"停止执行引擎失败: {str(e)}")


class ExecutionManager:
    """执行管理器 - 管理多个执行任务"""
    
    _instances: Dict[int, ExecutionEngine] = {}
    
    @classmethod
    def create_execution(cls, execution_id: int, db: AsyncSession) -> ExecutionEngine:
        """创建执行实例"""
        engine = ExecutionEngine(db)
        engine.execution_id = execution_id
        cls._instances[execution_id] = engine
        return engine
    
    @classmethod
    def get_execution(cls, execution_id: int) -> Optional[ExecutionEngine]:
        """获取执行实例"""
        return cls._instances.get(execution_id)
    
    @classmethod
    def stop_execution(cls, execution_id: int) -> bool:
        """停止执行"""
        engine = cls._instances.get(execution_id)
        if engine:
            engine.stop()
            return True
        return False
    
    @classmethod
    def remove_execution(cls, execution_id: int):
        """移除执行实例"""
        if execution_id in cls._instances:
            del cls._instances[execution_id]
