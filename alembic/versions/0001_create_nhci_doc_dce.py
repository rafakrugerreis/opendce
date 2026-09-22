"""
Criação da tabela nhci_doc_dce.
"""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nhci_doc_dce",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("serie", sa.Integer(), nullable=False),
        sa.Column("chave", sa.String(44), nullable=False),
        sa.Column("usuario", sa.String(100), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="GERADA"),
        sa.Column("c_stat", sa.String(10), nullable=True),
        sa.Column("motivo", sa.String(500), nullable=True),
        sa.Column("protocolo", sa.String(50), nullable=True),
        sa.Column("xml_assinado", sa.Text(), nullable=True),
        sa.Column("xml_original", sa.Text(), nullable=True),
        sa.Column("retorno_xml", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("transmitido_em", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("numero"),
        sa.UniqueConstraint("chave"),
    )


def downgrade() -> None:
    op.drop_table("nhci_doc_dce")
