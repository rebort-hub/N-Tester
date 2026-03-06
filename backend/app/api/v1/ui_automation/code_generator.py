"""
UI自动化模块 - 代码生成器
"""
from typing import List, Dict, Any


class CodeGenerator:
    """代码生成器"""
    
    @staticmethod
    def generate_code(
        page_object: Any,
        elements: List[Any],
        language: str = 'javascript',
        framework: str = 'playwright',
        include_comments: bool = True
    ) -> str:
        """生成代码"""
        if framework == 'playwright':
            if language == 'javascript':
                return CodeGenerator._generate_playwright_js(page_object, elements, include_comments)
            elif language == 'python':
                return CodeGenerator._generate_playwright_python(page_object, elements, include_comments)
        elif framework == 'selenium':
            if language == 'javascript':
                return CodeGenerator._generate_selenium_js(page_object, elements, include_comments)
            elif language == 'python':
                return CodeGenerator._generate_selenium_python(page_object, elements, include_comments)
        
        raise ValueError(f"不支持的组合: {framework} + {language}")
    
    @staticmethod
    def _generate_playwright_js(
        page_object: Any,
        elements: List[Any],
        include_comments: bool
    ) -> str:
        """生成Playwright JavaScript代码"""
        class_name = page_object.class_name or 'PageObject'
        
        code = []
        
        if include_comments:
            code.append(f"/**")
            code.append(f" * {page_object.name}")
            if page_object.description:
                code.append(f" * {page_object.description}")
            code.append(f" */")
        
        code.append(f"class {class_name} {{")
        code.append(f"  constructor(page) {{")
        code.append(f"    this.page = page;")
        
        # 生成元素定位器
        for element in elements:
            locator_value = element.locator_value
            element_name = element.name.replace(' ', '_').lower()
            
            if include_comments and element.description:
                code.append(f"    // {element.description}")
            
            if element.locator_strategy == 'css':
                code.append(f"    this.{element_name} = page.locator('{locator_value}');")
            elif element.locator_strategy == 'xpath':
                code.append(f"    this.{element_name} = page.locator('xpath={locator_value}');")
            elif element.locator_strategy == 'id':
                code.append(f"    this.{element_name} = page.locator('#{locator_value}');")
            elif element.locator_strategy == 'text':
                code.append(f"    this.{element_name} = page.getByText('{locator_value}');")
        
        code.append(f"  }}")
        
        # 生成操作方法
        if include_comments:
            code.append(f"")
            code.append(f"  /**")
            code.append(f"   * 页面操作方法")
            code.append(f"   */")
        
        for element in elements:
            element_name = element.name.replace(' ', '_').lower()
            
            if element.element_type == 'button':
                code.append(f"")
                code.append(f"  async click{element_name.title().replace('_', '')}() {{")
                code.append(f"    await this.{element_name}.click();")
                code.append(f"  }}")
            elif element.element_type == 'input':
                code.append(f"")
                code.append(f"  async fill{element_name.title().replace('_', '')}(value) {{")
                code.append(f"    await this.{element_name}.fill(value);")
                code.append(f"  }}")
        
        code.append(f"}}")
        code.append(f"")
        code.append(f"module.exports = {{ {class_name} }};")
        
        return '\n'.join(code)
    
    @staticmethod
    def _generate_playwright_python(
        page_object: Any,
        elements: List[Any],
        include_comments: bool
    ) -> str:
        """生成Playwright Python代码"""
        class_name = page_object.class_name or 'PageObject'
        
        code = []
        
        if include_comments:
            code.append(f'"""')
            code.append(f'{page_object.name}')
            if page_object.description:
                code.append(f'{page_object.description}')
            code.append(f'"""')
        
        code.append(f"from playwright.sync_api import Page")
        code.append(f"")
        code.append(f"")
        code.append(f"class {class_name}:")
        code.append(f"    def __init__(self, page: Page):")
        code.append(f"        self.page = page")
        
        # 生成元素定位器
        for element in elements:
            locator_value = element.locator_value
            element_name = element.name.replace(' ', '_').lower()
            
            if include_comments and element.description:
                code.append(f"        # {element.description}")
            
            if element.locator_strategy == 'css':
                code.append(f"        self.{element_name} = page.locator('{locator_value}')")
            elif element.locator_strategy == 'xpath':
                code.append(f"        self.{element_name} = page.locator('xpath={locator_value}')")
            elif element.locator_strategy == 'id':
                code.append(f"        self.{element_name} = page.locator('#{locator_value}')")
            elif element.locator_strategy == 'text':
                code.append(f"        self.{element_name} = page.get_by_text('{locator_value}')")
        
        # 生成操作方法
        for element in elements:
            element_name = element.name.replace(' ', '_').lower()
            method_name = element_name.replace('_', ' ').title().replace(' ', '')
            
            code.append(f"")
            if element.element_type == 'button':
                code.append(f"    def click_{element_name}(self):")
                if include_comments and element.description:
                    code.append(f"        \"\"\"{element.description}\"\"\"")
                code.append(f"        self.{element_name}.click()")
            elif element.element_type == 'input':
                code.append(f"    def fill_{element_name}(self, value: str):")
                if include_comments and element.description:
                    code.append(f"        \"\"\"{element.description}\"\"\"")
                code.append(f"        self.{element_name}.fill(value)")
        
        return '\n'.join(code)
    
    @staticmethod
    def _generate_selenium_js(
        page_object: Any,
        elements: List[Any],
        include_comments: bool
    ) -> str:
        """生成Selenium JavaScript代码"""
        class_name = page_object.class_name or 'PageObject'
        
        code = []
        
        if include_comments:
            code.append(f"/**")
            code.append(f" * {page_object.name}")
            if page_object.description:
                code.append(f" * {page_object.description}")
            code.append(f" */")
        
        code.append(f"const {{ By }} = require('selenium-webdriver');")
        code.append(f"")
        code.append(f"class {class_name} {{")
        code.append(f"  constructor(driver) {{")
        code.append(f"    this.driver = driver;")
        code.append(f"  }}")
        
        # 生成元素定位器方法
        for element in elements:
            locator_value = element.locator_value
            element_name = element.name.replace(' ', '_').lower()
            
            code.append(f"")
            if include_comments and element.description:
                code.append(f"  // {element.description}")
            
            code.append(f"  get{element_name.title().replace('_', '')}() {{")
            if element.locator_strategy == 'css':
                code.append(f"    return this.driver.findElement(By.css('{locator_value}'));")
            elif element.locator_strategy == 'xpath':
                code.append(f"    return this.driver.findElement(By.xpath('{locator_value}'));")
            elif element.locator_strategy == 'id':
                code.append(f"    return this.driver.findElement(By.id('{locator_value}'));")
            code.append(f"  }}")
        
        # 生成操作方法
        for element in elements:
            element_name = element.name.replace(' ', '_').lower()
            method_name = element_name.title().replace('_', '')
            
            code.append(f"")
            if element.element_type == 'button':
                code.append(f"  async click{method_name}() {{")
                code.append(f"    await this.get{method_name}().click();")
                code.append(f"  }}")
            elif element.element_type == 'input':
                code.append(f"  async fill{method_name}(value) {{")
                code.append(f"    await this.get{method_name}().sendKeys(value);")
                code.append(f"  }}")
        
        code.append(f"}}")
        code.append(f"")
        code.append(f"module.exports = {{ {class_name} }};")
        
        return '\n'.join(code)
    
    @staticmethod
    def _generate_selenium_python(
        page_object: Any,
        elements: List[Any],
        include_comments: bool
    ) -> str:
        """生成Selenium Python代码"""
        class_name = page_object.class_name or 'PageObject'
        
        code = []
        
        if include_comments:
            code.append(f'"""')
            code.append(f'{page_object.name}')
            if page_object.description:
                code.append(f'{page_object.description}')
            code.append(f'"""')
        
        code.append(f"from selenium.webdriver.common.by import By")
        code.append(f"from selenium.webdriver.remote.webdriver import WebDriver")
        code.append(f"")
        code.append(f"")
        code.append(f"class {class_name}:")
        code.append(f"    def __init__(self, driver: WebDriver):")
        code.append(f"        self.driver = driver")
        
        # 生成元素定位器
        for element in elements:
            locator_value = element.locator_value
            element_name = element.name.replace(' ', '_').lower()
            
            code.append(f"")
            if include_comments and element.description:
                code.append(f"    # {element.description}")
            
            code.append(f"    @property")
            code.append(f"    def {element_name}(self):")
            if element.locator_strategy == 'css':
                code.append(f"        return self.driver.find_element(By.CSS_SELECTOR, '{locator_value}')")
            elif element.locator_strategy == 'xpath':
                code.append(f"        return self.driver.find_element(By.XPATH, '{locator_value}')")
            elif element.locator_strategy == 'id':
                code.append(f"        return self.driver.find_element(By.ID, '{locator_value}')")
        
        # 生成操作方法
        for element in elements:
            element_name = element.name.replace(' ', '_').lower()
            
            code.append(f"")
            if element.element_type == 'button':
                code.append(f"    def click_{element_name}(self):")
                if include_comments and element.description:
                    code.append(f"        \"\"\"{element.description}\"\"\"")
                code.append(f"        self.{element_name}.click()")
            elif element.element_type == 'input':
                code.append(f"    def fill_{element_name}(self, value: str):")
                if include_comments and element.description:
                    code.append(f"        \"\"\"{element.description}\"\"\"")
                code.append(f"        self.{element_name}.send_keys(value)")
        
        return '\n'.join(code)



class AdvancedCodeGenerator:
    """高级代码生成器"""
    
    @staticmethod
    def generate_test_case_code(
        test_case: Any,
        steps: List[Any],
        elements: Dict[int, Any],
        language: str = 'javascript',
        framework: str = 'playwright'
    ) -> str:
        """生成测试用例代码"""
        if framework == 'playwright':
            if language == 'javascript':
                return AdvancedCodeGenerator._generate_playwright_test_js(test_case, steps, elements)
            elif language == 'python':
                return AdvancedCodeGenerator._generate_playwright_test_python(test_case, steps, elements)
        elif framework == 'selenium':
            if language == 'javascript':
                return AdvancedCodeGenerator._generate_selenium_test_js(test_case, steps, elements)
            elif language == 'python':
                return AdvancedCodeGenerator._generate_selenium_test_python(test_case, steps, elements)
        
        raise ValueError(f"不支持的组合: {framework} + {language}")
    
    @staticmethod
    def _generate_playwright_test_js(
        test_case: Any,
        steps: List[Any],
        elements: Dict[int, Any]
    ) -> str:
        """生成Playwright JavaScript测试用例代码"""
        code = []
        
        code.append(f"const {{ test, expect }} = require('@playwright/test');")
        code.append(f"")
        code.append(f"test.describe('{test_case.name}', () => {{")
        code.append(f"  test('{test_case.description or test_case.name}', async ({{ page }}) => {{")
        
        # 生成测试步骤
        for step in steps:
            element = elements.get(step.element_id) if step.element_id else None
            
            if step.action_type == 'navigate':
                code.append(f"    // {step.description or '导航'}")
                code.append(f"    await page.goto('{step.action_value}');")
            
            elif step.action_type == 'click' and element:
                code.append(f"    // {step.description or '点击'}")
                locator = AdvancedCodeGenerator._get_playwright_locator(element)
                code.append(f"    await page.locator('{locator}').click();")
            
            elif step.action_type == 'fill' and element:
                code.append(f"    // {step.description or '填充'}")
                locator = AdvancedCodeGenerator._get_playwright_locator(element)
                code.append(f"    await page.locator('{locator}').fill('{step.action_value}');")
            
            elif step.action_type == 'wait':
                code.append(f"    // {step.description or '等待'}")
                code.append(f"    await page.waitForTimeout({step.action_value or 1000});")
            
            # 添加断言
            if step.assertion_type:
                code.append(f"    // 断言: {step.assertion_type}")
                if step.assertion_type == 'visible' and element:
                    locator = AdvancedCodeGenerator._get_playwright_locator(element)
                    code.append(f"    await expect(page.locator('{locator}')).toBeVisible();")
                elif step.assertion_type == 'text' and element:
                    locator = AdvancedCodeGenerator._get_playwright_locator(element)
                    code.append(f"    await expect(page.locator('{locator}')).toHaveText('{step.assertion_value}');")
            
            code.append(f"")
        
        code.append(f"  }});")
        code.append(f"}});")
        
        return '\n'.join(code)
    
    @staticmethod
    def _generate_playwright_test_python(
        test_case: Any,
        steps: List[Any],
        elements: Dict[int, Any]
    ) -> str:
        """生成Playwright Python测试用例代码"""
        code = []
        
        code.append(f"import pytest")
        code.append(f"from playwright.sync_api import Page, expect")
        code.append(f"")
        code.append(f"")
        code.append(f"def test_{test_case.name.lower().replace(' ', '_')}(page: Page):")
        code.append(f'    """')
        code.append(f'    {test_case.description or test_case.name}')
        code.append(f'    """')
        
        # 生成测试步骤
        for step in steps:
            element = elements.get(step.element_id) if step.element_id else None
            
            if step.action_type == 'navigate':
                code.append(f"    # {step.description or '导航'}")
                code.append(f"    page.goto('{step.action_value}')")
            
            elif step.action_type == 'click' and element:
                code.append(f"    # {step.description or '点击'}")
                locator = AdvancedCodeGenerator._get_playwright_locator(element)
                code.append(f"    page.locator('{locator}').click()")
            
            elif step.action_type == 'fill' and element:
                code.append(f"    # {step.description or '填充'}")
                locator = AdvancedCodeGenerator._get_playwright_locator(element)
                code.append(f"    page.locator('{locator}').fill('{step.action_value}')")
            
            elif step.action_type == 'wait':
                code.append(f"    # {step.description or '等待'}")
                code.append(f"    page.wait_for_timeout({step.action_value or 1000})")
            
            # 添加断言
            if step.assertion_type:
                code.append(f"    # 断言: {step.assertion_type}")
                if step.assertion_type == 'visible' and element:
                    locator = AdvancedCodeGenerator._get_playwright_locator(element)
                    code.append(f"    expect(page.locator('{locator}')).to_be_visible()")
                elif step.assertion_type == 'text' and element:
                    locator = AdvancedCodeGenerator._get_playwright_locator(element)
                    code.append(f"    expect(page.locator('{locator}')).to_have_text('{step.assertion_value}')")
            
            code.append(f"")
        
        return '\n'.join(code)
    
    @staticmethod
    def _generate_selenium_test_js(
        test_case: Any,
        steps: List[Any],
        elements: Dict[int, Any]
    ) -> str:
        """生成Selenium JavaScript测试用例代码"""
        code = []
        
        code.append(f"const {{ Builder, By, until }} = require('selenium-webdriver');")
        code.append(f"")
        code.append(f"describe('{test_case.name}', function() {{")
        code.append(f"  let driver;")
        code.append(f"")
        code.append(f"  before(async function() {{")
        code.append(f"    driver = await new Builder().forBrowser('chrome').build();")
        code.append(f"  }});")
        code.append(f"")
        code.append(f"  after(async function() {{")
        code.append(f"    await driver.quit();")
        code.append(f"  }});")
        code.append(f"")
        code.append(f"  it('{test_case.description or test_case.name}', async function() {{")
        
        # 生成测试步骤
        for step in steps:
            element = elements.get(step.element_id) if step.element_id else None
            
            if step.action_type == 'navigate':
                code.append(f"    // {step.description or '导航'}")
                code.append(f"    await driver.get('{step.action_value}');")
            
            elif step.action_type == 'click' and element:
                code.append(f"    // {step.description or '点击'}")
                by_method, locator = AdvancedCodeGenerator._get_selenium_locator(element)
                code.append(f"    await driver.findElement(By.{by_method}('{locator}')).click();")
            
            elif step.action_type == 'fill' and element:
                code.append(f"    // {step.description or '填充'}")
                by_method, locator = AdvancedCodeGenerator._get_selenium_locator(element)
                code.append(f"    await driver.findElement(By.{by_method}('{locator}')).sendKeys('{step.action_value}');")
            
            code.append(f"")
        
        code.append(f"  }});")
        code.append(f"}});")
        
        return '\n'.join(code)
    
    @staticmethod
    def _generate_selenium_test_python(
        test_case: Any,
        steps: List[Any],
        elements: Dict[int, Any]
    ) -> str:
        """生成Selenium Python测试用例代码"""
        code = []
        
        code.append(f"import pytest")
        code.append(f"from selenium import webdriver")
        code.append(f"from selenium.webdriver.common.by import By")
        code.append(f"from selenium.webdriver.support.ui import WebDriverWait")
        code.append(f"from selenium.webdriver.support import expected_conditions as EC")
        code.append(f"")
        code.append(f"")
        code.append(f"@pytest.fixture")
        code.append(f"def driver():")
        code.append(f"    driver = webdriver.Chrome()")
        code.append(f"    yield driver")
        code.append(f"    driver.quit()")
        code.append(f"")
        code.append(f"")
        code.append(f"def test_{test_case.name.lower().replace(' ', '_')}(driver):")
        code.append(f'    """')
        code.append(f'    {test_case.description or test_case.name}')
        code.append(f'    """')
        
        # 生成测试步骤
        for step in steps:
            element = elements.get(step.element_id) if step.element_id else None
            
            if step.action_type == 'navigate':
                code.append(f"    # {step.description or '导航'}")
                code.append(f"    driver.get('{step.action_value}')")
            
            elif step.action_type == 'click' and element:
                code.append(f"    # {step.description or '点击'}")
                by_method, locator = AdvancedCodeGenerator._get_selenium_locator(element)
                code.append(f"    driver.find_element(By.{by_method}, '{locator}').click()")
            
            elif step.action_type == 'fill' and element:
                code.append(f"    # {step.description or '填充'}")
                by_method, locator = AdvancedCodeGenerator._get_selenium_locator(element)
                code.append(f"    driver.find_element(By.{by_method}, '{locator}').send_keys('{step.action_value}')")
            
            code.append(f"")
        
        return '\n'.join(code)
    
    @staticmethod
    def _get_playwright_locator(element: Any) -> str:
        """获取Playwright定位器"""
        if element.locator_strategy == 'css':
            return element.locator_value
        elif element.locator_strategy == 'xpath':
            return f"xpath={element.locator_value}"
        elif element.locator_strategy == 'id':
            return f"#{element.locator_value}"
        elif element.locator_strategy == 'text':
            return f"text={element.locator_value}"
        else:
            return element.locator_value
    
    @staticmethod
    def _get_selenium_locator(element: Any) -> tuple:
        """获取Selenium定位器"""
        if element.locator_strategy == 'css':
            return ('CSS_SELECTOR', element.locator_value)
        elif element.locator_strategy == 'xpath':
            return ('XPATH', element.locator_value)
        elif element.locator_strategy == 'id':
            return ('ID', element.locator_value)
        elif element.locator_strategy == 'name':
            return ('NAME', element.locator_value)
        elif element.locator_strategy == 'class':
            return ('CLASS_NAME', element.locator_value)
        else:
            return ('CSS_SELECTOR', element.locator_value)


class CodeFormatter:
    """代码格式化器"""
    
    @staticmethod
    def format_code(code: str, language: str) -> str:
        """格式化代码"""
        # 这里是格式化逻辑的占位符
        # 实际实现可以使用prettier(JS)或black(Python)
        
        # 简单的格式化：确保缩进一致
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 移除行尾空格
            line = line.rstrip()
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
