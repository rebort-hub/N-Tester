"""create app automation tables

Revision ID: 20260319_1200
Revises: 20260317_1200
Create Date: 2026-03-19 12:00:00.000000

创建 APP 自动化模块（迁移自 l-tester/views/app/app_model.py）所需表：
- app_menus
- app_scripts
- app_results
- app_result_lists
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_1200"
down_revision = "20260317_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_menus",
        sa.Column("name", sa.String(length=255), nullable=False, comment="名称"),
        sa.Column("pid", sa.BigInteger(), nullable=False, comment="父id"),
        sa.Column("type", sa.Integer(), nullable=False, comment="类型"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"]),
        mysql_charset="utf8",
        comment="APP自动化菜单表",
    )
    op.create_index(op.f("ix_app_menus_id"), "app_menus", ["id"], unique=False)

    op.create_table(
        "app_scripts",
        sa.Column("script", sa.JSON(), nullable=False, comment="脚本"),
        sa.Column("menu_id", sa.BigInteger(), nullable=False, comment="菜单ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="更新时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("menu_id"),
        sa.ForeignKeyConstraint(["menu_id"], ["app_menus.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"]),
        mysql_charset="utf8",
        comment="APP自动化脚本表",
    )
    op.create_index(op.f("ix_app_scripts_id"), "app_scripts", ["id"], unique=False)

    op.create_table(
        "app_result_lists",
        sa.Column("task_name", sa.String(length=255), nullable=False, comment="任务名称"),
        sa.Column("device_list", sa.JSON(), nullable=False, comment="设备列表"),
        sa.Column("result_id", sa.String(length=255), nullable=False, comment="结果id"),
        sa.Column("script_list", sa.JSON(), nullable=False, comment="脚本列表"),
        sa.Column("script_status", sa.JSON(), nullable=False, comment="脚本执行情况"),
        sa.Column("start_time", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
        sa.Column("end_time", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("result_id"),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"]),
        mysql_charset="utf8",
        comment="APP自动化结果汇总表",
    )
    op.create_index(op.f("ix_app_result_lists_id"), "app_result_lists", ["id"], unique=False)
    op.create_index("idx_app_result_lists_user", "app_result_lists", ["user_id"], unique=False)

    op.create_table(
        "app_results",
        sa.Column("device", sa.String(length=255), nullable=False, comment="设备"),
        sa.Column("result_id", sa.String(length=255), nullable=False, comment="结果id"),
        sa.Column("name", sa.String(length=255), nullable=False, comment="脚本名称"),
        sa.Column("status", sa.Integer(), nullable=False, comment="状态 0失败 1成功 2进行中(兼容旧)"),
        sa.Column("log", sa.Text(), nullable=True, comment="详情"),
        sa.Column("assert_value", sa.JSON(), nullable=True, comment="断言详情"),
        sa.Column("before_img", sa.Text(), nullable=True, comment="执行前截图地址"),
        sa.Column("after_img", sa.Text(), nullable=True, comment="执行后截图地址"),
        sa.Column("video", sa.Text(), nullable=True, comment="视频地址"),
        sa.Column("performance", sa.JSON(), nullable=True, comment="实时性能"),
        sa.Column("menu_id", sa.BigInteger(), nullable=False, comment="菜单ID"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="执行时间"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["menu_id"], ["app_menus.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"]),
        mysql_charset="utf8",
        comment="APP自动化执行结果表",
    )
    op.create_index(op.f("ix_app_results_id"), "app_results", ["id"], unique=False)
    op.create_index("idx_app_results_result", "app_results", ["result_id"], unique=False)
    op.create_index("idx_app_results_user_device", "app_results", ["user_id", "device"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_app_results_user_device", table_name="app_results")
    op.drop_index("idx_app_results_result", table_name="app_results")
    op.drop_index(op.f("ix_app_results_id"), table_name="app_results")
    op.drop_table("app_results")

    op.drop_index("idx_app_result_lists_user", table_name="app_result_lists")
    op.drop_index(op.f("ix_app_result_lists_id"), table_name="app_result_lists")
    op.drop_table("app_result_lists")

    op.drop_index(op.f("ix_app_scripts_id"), table_name="app_scripts")
    op.drop_table("app_scripts")

    op.drop_index(op.f("ix_app_menus_id"), table_name="app_menus")
    op.drop_table("app_menus")

