"""create app airtest images table

Revision ID: 20260319_1400
Revises: 20260319_1300
Create Date: 2026-03-19 14:00:00.000000

创建 APP 自动化图像库表（airtest_img）：
- app_airtest_images
"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_1400"
down_revision = "20260319_1300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_airtest_images",
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="图片名称"),
        sa.Column("file_path", sa.Text(), nullable=False, comment="图片地址"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.text("now()"), nullable=True, comment="创建时间"),
        sa.Column("menu_id", sa.BigInteger(), nullable=True, comment="所属菜单"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("creation_date", sa.DateTime(), nullable=True, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("updation_date", sa.DateTime(), nullable=True, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("enabled_flag", sa.Boolean(), nullable=False, comment="是否删除, 0 删除 1 非删除"),
        sa.Column("trace_id", sa.String(length=255), nullable=True, comment="trace_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["menu_id"], ["app_menus.id"]),
        mysql_charset="utf8",
        comment="APP自动化 Airtest 图像库",
    )
    op.create_index(op.f("ix_app_airtest_images_id"), "app_airtest_images", ["id"], unique=False)
    op.create_index("idx_app_airtest_images_menu", "app_airtest_images", ["menu_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_app_airtest_images_menu", table_name="app_airtest_images")
    op.drop_index(op.f("ix_app_airtest_images_id"), table_name="app_airtest_images")
    op.drop_table("app_airtest_images")

