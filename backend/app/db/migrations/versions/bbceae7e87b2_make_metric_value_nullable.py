"""make metric_value nullable

Revision ID: bbceae7e87b2
Revises: 75a4bc6c0eb5
Create Date: 2026-10-01 12:15:18.135113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bbceae7e87b2'
down_revision: Union[str, None] = '75a4bc6c0eb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely alter column to nullable=True
    op.alter_column('market_metrics', 'metric_value',
                    existing_type=sa.Float(),
                    nullable=True)


def downgrade() -> None:
    # Restore NOT NULL constraint. 
    # PostgreSQL will correctly fail this if any rows currently have metric_value = NULL,
    # satisfying the requirement to only restore if existing data permits it,
    # without silently coercing NULLs to zeros.
    op.alter_column('market_metrics', 'metric_value',
                    existing_type=sa.Float(),
                    nullable=False)
