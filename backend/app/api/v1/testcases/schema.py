"""
测试用例管理Schema
"""

from typing import Optional, List
from datetime import datetime
from pydantic import Field
from app.core.base_schema import BaseSchema, PageQuerySchema, TimestampSchema


# ========== 模块管理 ==========
class ModuleInfoBaseSchema(BaseSchema):
    """模块基础Schema"""
    name: str = Field(..., max_length=100, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")
    parent_id: Optional[int] = Field(None, description="父模块ID")
    sort_order: Optional[int] = Field(0, description="排序顺序")


class ModuleInfoCreateSchema(ModuleInfoBaseSchema):
    """模块创建Schema"""
    project_id: int = Field(..., description="所属项目ID")


class ModuleInfoUpdateSchema(BaseSchema):
    """模块更新Schema"""
    name: Optional[str] = Field(None, max_length=100, description="模块名称")
    description: Optional[str] = Field(None, description="模块描述")
    parent_id: Optional[int] = Field(None, description="父模块ID")
    sort_order: Optional[int] = Field(None, description="排序顺序")


class ModuleInfoOutSchema(ModuleInfoBaseSchema, TimestampSchema):
    """模块输出Schema"""
    id: int
    project_id: int
    testcase_count: Optional[int] = Field(0, description="用例数量")
    children: Optional[List['ModuleInfoOutSchema']] = Field(None, description="子模块列表")
    level: Optional[int] = Field(0, description="层级深度")
    path: Optional[str] = Field(None, description="模块路径")


class ModuleInfoQuerySchema(PageQuerySchema):
    """模块查询Schema"""
    project_id: int = Field(..., description="项目ID")
    name: Optional[str] = Field(None, description="模块名称")
    parent_id: Optional[int] = Field(None, description="父模块ID，null表示根模块")
    include_children: Optional[bool] = Field(True, description="是否包含子模块")


class ModuleTreeNodeSchema(BaseSchema):
    """模块树节点Schema"""
    id: int
    name: str
    project_id: int
    parent_id: Optional[int] = None
    description: Optional[str] = None
    sort_order: int = 0
    testcase_count: int = 0
    children: Optional[List['ModuleTreeNodeSchema']] = []
    level: int = 0


class ModuleImportSchema(BaseSchema):
    """模块导入Schema"""
    project_id: int = Field(..., description="目标项目ID")
    modules: List[dict] = Field(..., description="模块数据列表")
    override: Optional[bool] = Field(False, description="是否覆盖同名模块")


class ModuleExportSchema(BaseSchema):
    """模块导出Schema"""
    project_id: int = Field(..., description="项目ID")
    module_ids: Optional[List[int]] = Field(None, description="要导出的模块ID列表，为空则导出全部")
    include_testcases: Optional[bool] = Field(False, description="是否包含测试用例")


# 解决循环引用
ModuleInfoOutSchema.model_rebuild()
ModuleTreeNodeSchema.model_rebuild()


# ========== 测试用例步骤 ==========
class TestCaseStepBaseSchema(BaseSchema):
    """测试用例步骤基础Schema"""
    step_number: int = Field(..., description="步骤序号")
    action: str = Field(..., description="操作")
    expected: str = Field(..., description="预期结果")


class TestCaseStepCreateSchema(TestCaseStepBaseSchema):
    """测试用例步骤创建Schema"""
    pass


class TestCaseStepUpdateSchema(BaseSchema):
    """测试用例步骤更新Schema"""
    action: Optional[str] = None
    expected: Optional[str] = None


class TestCaseStepOutSchema(TestCaseStepBaseSchema, TimestampSchema):
    """测试用例步骤输出Schema"""
    id: int
    test_case_id: int


# ========== 测试用例 ==========
class TestCaseBaseSchema(BaseSchema):
    """测试用例基础Schema"""
    title: str = Field(..., min_length=1, max_length=500, description="用例标题")
    description: Optional[str] = Field(None, description="用例描述")
    preconditions: Optional[str] = Field(None, description="前置条件")
    expected_result: Optional[str] = Field(None, description="预期结果")
    priority: Optional[str] = Field("medium", description="优先级")
    status: Optional[str] = Field("draft", description="状态")
    test_type: Optional[str] = Field("functional", description="类型")
    tags: Optional[List[str]] = Field(None, description="标签")
    assignee_id: Optional[int] = Field(None, description="指派人ID")
    module_id: Optional[int] = Field(None, description="模块ID")


class TestCaseCreateSchema(TestCaseBaseSchema):
    """测试用例创建Schema"""
    steps: Optional[List[TestCaseStepCreateSchema]] = Field(None, description="测试步骤")


class TestCaseUpdateSchema(BaseSchema):
    """测试用例更新Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    preconditions: Optional[str] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    test_type: Optional[str] = None
    tags: Optional[List[str]] = None
    assignee_id: Optional[int] = None
    module_id: Optional[int] = None
    steps: Optional[List[TestCaseStepCreateSchema]] = None


class TestCaseOutSchema(TestCaseBaseSchema, TimestampSchema):
    """测试用例输出Schema"""
    id: int
    project_id: int
    author_id: int
    author_name: Optional[str] = None
    assignee_name: Optional[str] = None
    module_name: Optional[str] = None
    creation_date: datetime
    updation_date: datetime
    steps: Optional[List[TestCaseStepOutSchema]] = []
    version_ids: Optional[List[int]] = []


class TestCaseQuerySchema(PageQuerySchema):
    """测试用例查询Schema"""
    project_id: int = Field(..., description="项目ID")
    title: Optional[str] = Field(None, description="用例标题")
    status: Optional[str] = Field(None, description="状态")
    priority: Optional[str] = Field(None, description="优先级")
    test_type: Optional[str] = Field(None, description="类型")
    author_id: Optional[int] = Field(None, description="作者ID")
    version_id: Optional[int] = Field(None, description="版本ID")
    module_id: Optional[int] = Field(None, description="模块ID")


# ========== 版本 ==========
class VersionBaseSchema(BaseSchema):
    """版本基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="版本名称")
    description: Optional[str] = Field(None, description="版本描述")
    is_baseline: Optional[bool] = Field(False, description="是否基线版本")


class VersionCreateSchema(VersionBaseSchema):
    """版本创建Schema"""
    project_ids: Optional[List[int]] = Field(None, description="关联项目ID列表")


class VersionUpdateSchema(BaseSchema):
    """版本更新Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_baseline: Optional[bool] = None


class VersionOutSchema(VersionBaseSchema, TimestampSchema):
    """版本输出Schema"""
    id: int
    creation_date: datetime
    updation_date: datetime
    project_count: Optional[int] = 0
    testcase_count: Optional[int] = 0


class VersionQuerySchema(PageQuerySchema):
    """版本查询Schema"""
    name: Optional[str] = Field(None, description="版本名称")
    is_baseline: Optional[bool] = Field(None, description="是否基线版本")
    project_id: Optional[int] = Field(None, description="项目ID")


# ========== 版本关联 ==========
class VersionAssociationSchema(BaseSchema):
    """版本关联Schema"""
    version_id: int = Field(..., description="版本ID")
    testcase_ids: List[int] = Field(..., description="测试用例ID列表")
