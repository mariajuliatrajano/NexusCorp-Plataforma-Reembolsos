from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.models import Role, ReimbursementStatus

class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)

class DepartmentOut(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: str = Field(min_length=5, max_length=180)
    password: str = Field(min_length=8, max_length=128)
    role: Role
    department_id: int

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: Role
    department_id: int
    model_config = ConfigDict(from_attributes=True)

class LoginInput(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ReimbursementCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    expense_date: date
    justification: str = Field(min_length=5, max_length=3000)
    receipt_reference: str = Field(min_length=2, max_length=180)

class ReimbursementUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=2, max_length=40)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    expense_date: date | None = None
    justification: str | None = Field(default=None, min_length=5, max_length=3000)
    receipt_reference: str | None = Field(default=None, min_length=2, max_length=180)

class DecisionInput(BaseModel):
    observation: str | None = Field(default=None, max_length=3000)

class ReimbursementOut(BaseModel):
    id: int
    requester_id: int
    category: str
    amount: Decimal
    expense_date: date
    justification: str
    receipt_reference: str
    status: ReimbursementStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class HistoryOut(BaseModel):
    id: int
    reimbursement_id: int
    responsible_user_id: int
    stage: str
    decision: str
    observation: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
