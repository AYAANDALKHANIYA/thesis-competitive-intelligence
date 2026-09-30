"""add analysis_id to metric, insight, sentiment

Revision ID: 75a4bc6c0eb5
Revises: 146dc3703d3d
Create Date: 2026-09-30 19:37:09.766075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75a4bc6c0eb5'
down_revision: Union[str, None] = '146dc3703d3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # market_metrics
    op.add_column('market_metrics', sa.Column('analysis_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_market_metrics_analysis_id', 'market_metrics', 'analysis_runs', ['analysis_id'], ['id'], ondelete='CASCADE')

    # insights
    op.add_column('insights', sa.Column('analysis_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_insights_analysis_id', 'insights', 'analysis_runs', ['analysis_id'], ['id'], ondelete='CASCADE')

    # sentiment_results
    op.add_column('sentiment_results', sa.Column('analysis_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_sentiment_results_analysis_id', 'sentiment_results', 'analysis_runs', ['analysis_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # sentiment_results
    op.drop_constraint('fk_sentiment_results_analysis_id', 'sentiment_results', type_='foreignkey')
    op.drop_column('sentiment_results', 'analysis_id')

    # insights
    op.drop_constraint('fk_insights_analysis_id', 'insights', type_='foreignkey')
    op.drop_column('insights', 'analysis_id')

    # market_metrics
    op.drop_constraint('fk_market_metrics_analysis_id', 'market_metrics', type_='foreignkey')
    op.drop_column('market_metrics', 'analysis_id')
