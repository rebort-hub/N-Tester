"""modify_file_content_to_longblob

Revision ID: 28632f2b9509
Revises: add_file_content_column
Create Date: 2026-03-12 18:12:31.892675

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28632f2b9509'
down_revision = 'add_file_content_column'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 修改 file_content 字段类型为 LONGBLOB 以支持更大的文件
    op.execute("ALTER TABLE sys_file MODIFY COLUMN file_content LONGBLOB COMMENT '文件二进制内容（用于数据库存储模式）'")


def downgrade() -> None:
    # 回滚到原来的 BLOB 类型
    op.execute("ALTER TABLE sys_file MODIFY COLUMN file_content BLOB COMMENT '文件二进制内容（用于数据库存储模式）'")
