"""seed default root for web management tree (element + web script menu)

Revision ID: 20260313_1700
Revises: a1b2c3d4e5f6
Create Date: 2026-03-13 17:00:00.000000

元素管理、Web 自动化左侧树需要 pid=0 的默认根目录，否则无法新增子菜单。
本迁移向 web_management_element_menus、web_management_menus 各插入一条根节点（若不存在）。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260313_1700"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 元素管理树：默认根目录（pid=0, type=0 文件夹）
    conn.execute(
        sa.text(
            """
        INSERT INTO web_management_element_menus
          (name, pid, type, element_id, creation_date, enabled_flag)
        SELECT '默认分组', 0, 0, NULL, NOW(), 1
        WHERE NOT EXISTS (
            SELECT 1 FROM web_management_element_menus
            WHERE pid = 0 AND enabled_flag = 1
        )
        """
        )
    )

    # Web 脚本菜单树：默认根目录（pid=0, type=0 文件夹）
    conn.execute(
        sa.text(
            """
        INSERT INTO web_management_menus
          (name, pid, type, creation_date, enabled_flag)
        SELECT '默认分组', 0, 0, NOW(), 1
        WHERE NOT EXISTS (
            SELECT 1 FROM web_management_menus
            WHERE pid = 0 AND enabled_flag = 1
        )
        """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()

    # 仅删除 pid=0 且 name 为默认的根（避免误删用户自建根）
    conn.execute(
        sa.text(
            """
        UPDATE web_management_element_menus
        SET enabled_flag = 0
        WHERE pid = 0 AND name = '默认分组' AND enabled_flag = 1
        """
        )
    )
    conn.execute(
        sa.text(
            """
        UPDATE web_management_menus
        SET enabled_flag = 0
        WHERE pid = 0 AND name = '默认分组' AND enabled_flag = 1
        """
        )
    )
