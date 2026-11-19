from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import (
    String, Integer, Date, DateTime, ForeignKey, Numeric, Text,
    Enum, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum

class Role(str, enum.Enum):
    COLLABORATOR = "COLABORADOR"
    MANAGER = "GESTOR"
    FINANCE = "FINANCEIRO"
    ADMIN = "ADMIN"

class ReimbursementStatus(str, enum.Enum):
    DRAFT = "RASCUNHO"
    WAITING_MANAGER = "AGUARDANDO_GESTOR"
    WAITING_FINANCE = "AGUARDANDO_FINANCEIRO"
    APPROVED = "APROVADA"
    PAID = "PAGA"
    REJECTED = "RECUSADA"

class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.COLLABORATOR)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    department = relationship("Department", back_populates="users")
    reimbursements = relationship("Reimbursement", back_populates="requester")

class Reimbursement(Base):
    __tablename__ = "reimbursements"
    __table_args__ = (
        UniqueConstraint("requester_id", "receipt_reference", name="uq_receipt_per_requester"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    receipt_reference: Mapped[str] = mapped_column(String(180), nullable=False)
    status: Mapped[ReimbursementStatus] = mapped_column(
        Enum(ReimbursementStatus), nullable=False, default=ReimbursementStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    requester = relationship("User", back_populates="reimbursements")
    history = relationship("AnalysisHistory", back_populates="reimbursement",
                           order_by="AnalysisHistory.created_at", cascade="all, delete-orphan")

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reimbursement_id: Mapped[int] = mapped_column(ForeignKey("reimbursements.id"), nullable=False, index=True)
    responsible_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    decision: Mapped[str] = mapped_column(String(40), nullable=False)
    observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    reimbursement = relationship("Reimbursement", back_populates="history")
    responsible = relationship("User")
