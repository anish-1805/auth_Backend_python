"""Add subscription and chat message tables

Revision ID: add_subscription_tables
Revises: 
Create Date: 2024-02-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_subscription_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('plan', sa.Enum('free', 'basic', 'standard', 'premium', name='subscriptionplan'), nullable=False, server_default='free'),
        sa.Column('status', sa.Enum('active', 'canceled', 'expired', 'past_due', name='subscriptionstatus'), nullable=False, server_default='active'),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('stripe_price_id', sa.String(255), nullable=True),
        sa.Column('messages_per_week', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('messages_used_this_week', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('week_reset_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('createdAt', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updatedAt', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('createdAt', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
    )


def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('subscriptions')
    op.execute('DROP TYPE subscriptionplan')
    op.execute('DROP TYPE subscriptionstatus')
