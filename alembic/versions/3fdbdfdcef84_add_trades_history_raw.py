"""add trades history raw

Revision ID: 3fdbdfdcef84
Revises: af872e1a3e86
Create Date: 2025-01-05 13:02:55.782752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '3fdbdfdcef84'
down_revision: Union[str, None] = 'af872e1a3e86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('bybit_trades_history_raw',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('symbol', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('category', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('order_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('underlying_price', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('order_link_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('side', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('index_price', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('order_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('stop_order_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('leaves_qty', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_time', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('fee_currency', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_maker', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_fee', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('fee_rate', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('trade_iv', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('block_trade_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('mark_price', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_price', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('mark_iv', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('order_qty', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('order_price', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_value', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('exec_qty', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('closed_size', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('seq', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('bybit_trades_history_raw')
    # ### end Alembic commands ###
