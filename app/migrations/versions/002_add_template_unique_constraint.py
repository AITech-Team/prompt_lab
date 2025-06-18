"""add template unique constraint

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # 先删除旧的唯一约束（如果存在）
    try:
        op.drop_constraint('uix_name', 'prompt_templates', type_='unique')
    except:
        pass
    
    # 添加新的组合唯一约束
    op.create_unique_constraint(
        'uix_name_not_deleted',
        'prompt_templates',
        ['name', 'is_deleted']
    )

def downgrade():
    # 删除新的组合唯一约束
    op.drop_constraint('uix_name_not_deleted', 'prompt_templates', type_='unique')
    
    # 恢复旧的唯一约束
    op.create_unique_constraint('uix_name', 'prompt_templates', ['name']) 