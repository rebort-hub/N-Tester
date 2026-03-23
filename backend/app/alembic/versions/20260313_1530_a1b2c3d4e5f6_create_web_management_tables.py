"""create web management tables

Revision ID: a1b2c3d4e5f6
Revises: 20260313_1200
Create Date: 2026-03-13 15:30:00.000000

Web管理模块（Web UI 自动化迁移）建表：
- web_management_* 表
- 含 pid_list 字段，用于 stop_web_script 进程终止

"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "20260313_1200"
branch_labels = None
depends_on = None


def _base_columns():
    return [
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
    ]


def upgrade() -> None:
    # Web 脚本菜单
    op.create_table(
        "web_management_menus",
        sa.Column("name", sa.String(length=255), nullable=False, comment="菜单名称"),
        sa.Column("pid", sa.BigInteger(), nullable=False, comment="父菜单ID"),
        sa.Column("type", sa.Integer(), nullable=False, comment="菜单类型: 0-文件夹, 1-脚本组, 2-脚本"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        mysql_charset="utf8",
    )

    # Web 脚本内容（menu_id 唯一）
    op.create_table(
        "web_management_scripts",
        sa.Column("script", sa.JSON(), nullable=False, comment="脚本步骤"),
        sa.Column("menu_id", sa.BigInteger(), nullable=False, comment="菜单ID"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("menu_id"),
        mysql_charset="utf8",
    )

    # Web 元素菜单
    op.create_table(
        "web_management_element_menus",
        sa.Column("name", sa.String(length=255), nullable=False, comment="元素菜单名称"),
        sa.Column("pid", sa.BigInteger(), nullable=False, comment="父菜单ID"),
        sa.Column("type", sa.Integer(), nullable=False, comment="菜单类型"),
        sa.Column("element_id", sa.BigInteger(), nullable=True, comment="元素ID"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        mysql_charset="utf8",
    )

    # Web 元素
    op.create_table(
        "web_management_elements",
        sa.Column("name", sa.String(length=255), nullable=False, comment="元素名称"),
        sa.Column("element", sa.JSON(), nullable=False, comment="元素选择器信息"),
        sa.Column("menu_id", sa.BigInteger(), nullable=True, comment="菜单ID"),
        sa.Column("element_type", sa.String(length=50), nullable=True, comment="元素类型"),
        sa.Column("locator_strategy", sa.String(length=50), nullable=True, comment="定位策略"),
        sa.Column("locator_value", sa.String(length=1000), nullable=True, comment="定位器值"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    # Web 脚本集
    op.create_table(
        "web_management_groups",
        sa.Column("name", sa.String(length=255), nullable=False, comment="脚本集名称"),
        sa.Column("script", sa.JSON(), nullable=True, comment="脚本集配置"),
        sa.Column("description", sa.String(length=255), nullable=True, comment="脚本集描述"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        mysql_charset="utf8",
    )

    # Web 执行汇总
    op.create_table(
        "web_management_result_lists",
        sa.Column("task_name", sa.String(length=255), nullable=False, comment="任务名称"),
        sa.Column("result_id", sa.String(length=255), nullable=False, comment="执行ID"),
        sa.Column("script_list", sa.JSON(), nullable=False, comment="脚本列表"),
        sa.Column("browser_list", sa.JSON(), nullable=False, comment="浏览器列表"),
        sa.Column("result", sa.JSON(), nullable=False, comment="执行结果"),
        sa.Column("pid_list", sa.JSON(), nullable=True, comment="执行进程PID列表（兼容旧 stop_web_script）"),
        sa.Column("start_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True, comment="开始时间"),
        sa.Column("end_time", sa.DateTime(), nullable=True, comment="结束时间"),
        sa.Column("status", sa.Integer(), nullable=True, comment="执行状态: 0-执行中, 1-完成"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )

    # Web 执行详情
    op.create_table(
        "web_management_result_details",
        sa.Column("name", sa.String(length=255), nullable=False, comment="脚本名称"),
        sa.Column("result_id", sa.String(length=255), nullable=False, comment="执行ID"),
        sa.Column("browser", sa.String(length=255), nullable=False, comment="浏览器类型"),
        sa.Column("log", sa.Text(), nullable=False, comment="执行日志"),
        sa.Column("status", sa.Integer(), nullable=False, comment="执行状态: 0-失败, 1-成功"),
        sa.Column("before_img", sa.String(length=255), nullable=True, comment="执行前截图"),
        sa.Column("after_img", sa.String(length=255), nullable=True, comment="执行后截图"),
        sa.Column("video", sa.String(length=255), nullable=True, comment="视频地址"),
        sa.Column("trace", sa.String(length=255), nullable=True, comment="Playwright trace文件"),
        sa.Column("assert_result", sa.JSON(), nullable=False, comment="断言结果"),
        sa.Column("menu_id", sa.BigInteger(), nullable=True, comment="脚本菜单ID"),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
    )


def downgrade() -> None:
    op.drop_table("web_management_result_details")
    op.drop_table("web_management_result_lists")
    op.drop_table("web_management_groups")
    op.drop_table("web_management_elements")
    op.drop_table("web_management_element_menus")
    op.drop_table("web_management_scripts")
    op.drop_table("web_management_menus")

