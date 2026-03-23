"""create app mitmproxy tables

Revision ID: 20260317_1200
Revises: 20260313_1800
Create Date: 2026-03-17 12:00:00.000000

创建 APP 抓包（mitmproxy）模块所需表：
- app_mitmproxy_api
"""

from alembic import op
import sqlalchemy as sa


revision = "20260317_1200"
down_revision = "20260313_1800"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_mitmproxy_api",
        sa.Column("result_id", sa.String(length=255), nullable=False, comment="结果ID"),
        sa.Column("device_id", sa.Integer(), nullable=False, comment="设备ID（app_devices.id）"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("url", sa.Text(), nullable=False, comment="接口请求地址"),
        sa.Column("method", sa.String(length=255), nullable=False, comment="请求方法"),
        sa.Column("request_body", sa.JSON(), nullable=True, comment="请求体"),
        sa.Column("request_headers", sa.JSON(), nullable=True, comment="请求头"),
        sa.Column("response_headers", sa.JSON(), nullable=True, comment="响应头"),
        sa.Column("response_body", sa.JSON(), nullable=True, comment="响应体"),
        sa.Column("status", sa.Integer(), nullable=False, comment="状态(0失败/1成功)"),
        sa.Column("res_time", sa.String(length=255), nullable=True, comment="响应时间(ms)"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.ForeignKeyConstraint(["device_id"], ["app_devices.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_charset="utf8",
        comment="mitmproxy 抓包接口记录表",
    )

    op.create_index(op.f("ix_app_mitmproxy_api_id"), "app_mitmproxy_api", ["id"], unique=False)
    op.create_index("idx_app_mitmproxy_api_user_device", "app_mitmproxy_api", ["user_id", "device_id"], unique=False)
    op.create_index("idx_app_mitmproxy_api_result", "app_mitmproxy_api", ["result_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_app_mitmproxy_api_result", table_name="app_mitmproxy_api")
    op.drop_index("idx_app_mitmproxy_api_user_device", table_name="app_mitmproxy_api")
    op.drop_index(op.f("ix_app_mitmproxy_api_id"), table_name="app_mitmproxy_api")
    op.drop_table("app_mitmproxy_api")

