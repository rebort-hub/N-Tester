"""create api automation tables

Revision ID: 587c5ffd5ff7
Revises: c69d08969b1e
Create Date: 2026-03-12 15:18:30.486442

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "587c5ffd5ff7"
down_revision = "c69d08969b1e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 接口自动化模块（迁移后）建表：仅包含 api_automation_* 表
    op.create_table(
        "api_automation_apis",
        sa.Column("url", sa.String(length=255), nullable=False, comment="接口URL"),
        sa.Column("req", sa.JSON(), nullable=True, comment="请求配置"),
        sa.Column("document", sa.JSON(), nullable=True, comment="接口文档"),
        sa.Column("api_service_id", sa.BigInteger(), nullable=False, comment="服务ID"),
        sa.Column("name", sa.String(length=255), nullable=True, comment="接口名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="接口描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_codes",
        sa.Column("code", sa.String(length=255), nullable=False, comment="错误码"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="错误码名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="错误码描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_databases",
        sa.Column("name", sa.String(length=255), nullable=False, comment="数据库名称"),
        sa.Column("config", sa.JSON(), nullable=True, comment="数据库配置"),
        sa.Column("db_type", sa.String(length=50), nullable=True, comment="数据库类型"),
        sa.Column("host", sa.String(length=255), nullable=True, comment="主机地址"),
        sa.Column("port", sa.Integer(), nullable=True, comment="端口"),
        sa.Column("database_name", sa.String(length=255), nullable=True, comment="数据库名"),
        sa.Column("username", sa.String(length=255), nullable=True, comment="用户名"),
        sa.Column("password", sa.String(length=500), nullable=True, comment="密码"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_edits",
        sa.Column("api_id", sa.BigInteger(), nullable=False, comment="接口ID"),
        sa.Column("edit", sa.JSON(), nullable=True, comment="变更内容"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_environments",
        sa.Column("name", sa.String(length=255), nullable=False, comment="环境名称"),
        sa.Column("config", sa.JSON(), nullable=True, comment="环境配置"),
        sa.Column("variable", sa.JSON(), nullable=True, comment="环境变量"),
        sa.Column("description", sa.Text(), nullable=True, comment="环境描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_functions",
        sa.Column("name", sa.String(length=255), nullable=False, comment="公共函数名称"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="公共函数描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_menus",
        sa.Column("name", sa.String(length=255), nullable=False, comment="菜单名称"),
        sa.Column("type", sa.Integer(), nullable=False, comment="菜单类型"),
        sa.Column("pid", sa.BigInteger(), nullable=False, comment="父菜单ID"),
        sa.Column("api_id", sa.BigInteger(), nullable=True, comment="接口ID"),
        sa.Column("api_service_id", sa.BigInteger(), nullable=False, comment="服务ID"),
        sa.Column("status", sa.Integer(), nullable=False, comment="状态"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_params",
        sa.Column("name", sa.String(length=255), nullable=False, comment="参数名称"),
        sa.Column("value", sa.JSON(), nullable=True, comment="参数值"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_projects",
        sa.Column("name", sa.String(length=255), nullable=False, comment="项目名称"),
        sa.Column("img", sa.String(length=255), nullable=True, comment="项目图标"),
        sa.Column("description", sa.Text(), nullable=True, comment="项目描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_results",
        sa.Column("req", sa.JSON(), nullable=True, comment="请求数据"),
        sa.Column("res", sa.JSON(), nullable=True, comment="响应数据"),
        sa.Column("api_id", sa.BigInteger(), nullable=False, comment="接口ID"),
        sa.Column("status_code", sa.Integer(), nullable=True, comment="状态码"),
        sa.Column("response_time", sa.Float(), nullable=True, comment="响应时间"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="错误信息"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_script_result_lists",
        sa.Column("result_id", sa.BigInteger(), nullable=False, comment="执行ID"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="场景名称"),
        sa.Column("script", sa.JSON(), nullable=True, comment="场景配置"),
        sa.Column("config", sa.JSON(), nullable=True, comment="执行配置"),
        sa.Column("result", sa.JSON(), nullable=True, comment="执行结果"),
        sa.Column("start_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True, comment="开始时间"),
        sa.Column("end_time", sa.DateTime(), nullable=True, comment="结束时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_script_results",
        sa.Column("name", sa.String(length=255), nullable=False, comment="步骤名称"),
        sa.Column("uuid", sa.String(length=255), nullable=True, comment="唯一标识"),
        sa.Column("menu_id", sa.String(length=255), nullable=False, comment="菜单ID"),
        sa.Column("result_id", sa.BigInteger(), nullable=False, comment="执行ID"),
        sa.Column("status", sa.Integer(), nullable=True, comment="执行状态"),
        sa.Column("req", sa.JSON(), nullable=True, comment="请求数据"),
        sa.Column("res", sa.JSON(), nullable=True, comment="响应数据"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_scripts",
        sa.Column("name", sa.String(length=255), nullable=False, comment="场景名称"),
        sa.Column("type", sa.Integer(), nullable=True, comment="场景类型"),
        sa.Column("script", sa.JSON(), nullable=False, comment="场景步骤"),
        sa.Column("config", sa.JSON(), nullable=True, comment="场景配置"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="场景描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_services",
        sa.Column("name", sa.String(length=255), nullable=False, comment="服务名称"),
        sa.Column("api_project_id", sa.BigInteger(), nullable=False, comment="项目ID"),
        sa.Column("img", sa.String(length=255), nullable=True, comment="服务图标"),
        sa.Column("description", sa.Text(), nullable=True, comment="服务描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_updates",
        sa.Column("req", sa.JSON(), nullable=True, comment="变更内容"),
        sa.Column("api_id", sa.BigInteger(), nullable=False, comment="接口ID"),
        sa.Column("api_service_id", sa.BigInteger(), nullable=False, comment="服务ID"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    op.create_table(
        "api_automation_variables",
        sa.Column("name", sa.String(length=255), nullable=False, comment="变量名"),
        sa.Column("value", sa.String(length=255), nullable=False, comment="变量值"),
        sa.Column("description", sa.Text(), nullable=True, comment="变量描述"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )


def downgrade() -> None:
    # 逆序删除
    op.drop_table("api_automation_variables")
    op.drop_table("api_automation_updates")
    op.drop_table("api_automation_services")
    op.drop_table("api_automation_scripts")
    op.drop_table("api_automation_script_results")
    op.drop_table("api_automation_script_result_lists")
    op.drop_table("api_automation_results")
    op.drop_table("api_automation_projects")
    op.drop_table("api_automation_params")
    op.drop_table("api_automation_menus")
    op.drop_table("api_automation_functions")
    op.drop_table("api_automation_environments")
    op.drop_table("api_automation_edits")
    op.drop_table("api_automation_databases")
    op.drop_table("api_automation_codes")
    op.drop_table("api_automation_apis")

