from datetime import date
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.database import Base, engine, get_db
from app.models import Department, User, Reimbursement, AnalysisHistory, Role, ReimbursementStatus
from app.schemas import (DepartmentCreate, DepartmentOut, UserCreate, UserOut, LoginInput,
    TokenOut, ReimbursementCreate, ReimbursementUpdate, ReimbursementOut, DecisionInput, HistoryOut)
from app.security import hash_password, verify_password, create_access_token, get_current_user, require_roles

Base.metadata.create_all(bind=engine)
app = FastAPI(title="NexusCorp - API de Gestão de Reembolsos", version="1.0.0",
              description="API REST com autenticação JWT, autorização por perfil e trilha de auditoria.")

def add_history(db, reimbursement_id, user_id, stage, decision, observation=None):
    db.add(AnalysisHistory(reimbursement_id=reimbursement_id, responsible_user_id=user_id,
                           stage=stage, decision=decision, observation=observation))

def get_reimbursement_or_404(db, reimbursement_id):
    item = db.query(Reimbursement).options(joinedload(Reimbursement.requester)).filter(
        Reimbursement.id == reimbursement_id).first()
    if not item:
        raise HTTPException(404, "Solicitação não encontrada.")
    return item

def ensure_visible(item, user):
    if user.role == Role.ADMIN:
        return
    if user.role == Role.COLLABORATOR and item.requester_id != user.id:
        raise HTTPException(404, "Solicitação não encontrada.")
    if user.role == Role.MANAGER and item.requester.department_id != user.department_id:
        raise HTTPException(404, "Solicitação não encontrada.")

@app.get("/", tags=["Sistema"])
def root():
    return {"message": "NexusCorp API operacional", "docs": "/docs"}

@app.post("/auth/login", response_model=TokenOut, tags=["Autenticação"])
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "E-mail ou senha inválidos.")
    return {"access_token": create_access_token(user)}

@app.post("/departments", response_model=DepartmentOut, status_code=201, tags=["Administração"])
def create_department(data: DepartmentCreate, db: Session = Depends(get_db),
                      admin: User = Depends(require_roles(Role.ADMIN))):
    department = Department(name=data.name.strip())
    db.add(department)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Departamento já cadastrado.")
    db.refresh(department)
    return department

@app.get("/departments", response_model=list[DepartmentOut], tags=["Administração"])
def list_departments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Department).order_by(Department.name).all()

@app.post("/users", response_model=UserOut, status_code=201, tags=["Administração"])
def create_user(data: UserCreate, db: Session = Depends(get_db),
                admin: User = Depends(require_roles(Role.ADMIN))):
    if not db.get(Department, data.department_id):
        raise HTTPException(404, "Departamento não encontrado.")
    user = User(name=data.name.strip(), email=data.email.lower().strip(),
                password_hash=hash_password(data.password), role=data.role,
                department_id=data.department_id)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "E-mail já cadastrado.")
    db.refresh(user)
    return user

@app.get("/users/me", response_model=UserOut, tags=["Usuários"])
def me(user: User = Depends(get_current_user)):
    return user

@app.post("/reimbursements", response_model=ReimbursementOut, status_code=201, tags=["Reembolsos"])
def create_reimbursement(data: ReimbursementCreate, db: Session = Depends(get_db),
                         user: User = Depends(require_roles(Role.COLLABORATOR))):
    if data.expense_date > date.today():
        raise HTTPException(422, "A data da despesa não pode ser futura.")
    duplicate = db.query(Reimbursement).filter(
        Reimbursement.requester_id == user.id,
        Reimbursement.receipt_reference == data.receipt_reference.strip()
    ).first()
    if duplicate:
        raise HTTPException(409, "Já existe despesa deste colaborador com essa referência de comprovante.")
    item = Reimbursement(requester_id=user.id, category=data.category.strip(),
        amount=data.amount, expense_date=data.expense_date, justification=data.justification.strip(),
        receipt_reference=data.receipt_reference.strip(), status=ReimbursementStatus.DRAFT)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/reimbursements", response_model=list[ReimbursementOut], tags=["Reembolsos"])
def list_reimbursements(status_filter: ReimbursementStatus | None = Query(default=None, alias="status"),
                        category: str | None = None, department_id: int | None = None,
                        db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Reimbursement).join(User, Reimbursement.requester_id == User.id)
    if user.role == Role.COLLABORATOR:
        query = query.filter(Reimbursement.requester_id == user.id)
    elif user.role == Role.MANAGER:
        query = query.filter(User.department_id == user.department_id)
    elif user.role == Role.FINANCE:
        # Financeiro visualiza solicitações que chegaram à etapa financeira ou foram encerradas.
        query = query.filter(Reimbursement.status.in_([
            ReimbursementStatus.WAITING_FINANCE, ReimbursementStatus.APPROVED,
            ReimbursementStatus.PAID, ReimbursementStatus.REJECTED]))
    if department_id is not None:
        if user.role not in (Role.FINANCE, Role.ADMIN) and department_id != user.department_id:
            raise HTTPException(403, "Filtro de departamento não autorizado.")
        query = query.filter(User.department_id == department_id)
    if status_filter:
        query = query.filter(Reimbursement.status == status_filter)
    if category:
        query = query.filter(Reimbursement.category == category)
    return query.order_by(Reimbursement.created_at.desc()).all()

@app.get("/reimbursements/{reimbursement_id}", response_model=ReimbursementOut, tags=["Reembolsos"])
def get_reimbursement(reimbursement_id: int, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    item = get_reimbursement_or_404(db, reimbursement_id)
    ensure_visible(item, user)
    if user.role == Role.FINANCE and item.status == ReimbursementStatus.DRAFT:
        raise HTTPException(404, "Solicitação não encontrada.")
    return item

@app.patch("/reimbursements/{reimbursement_id}", response_model=ReimbursementOut, tags=["Reembolsos"])
def update_reimbursement(reimbursement_id: int, data: ReimbursementUpdate,
                         db: Session = Depends(get_db),
                         user: User = Depends(require_roles(Role.COLLABORATOR))):
    item = get_reimbursement_or_404(db, reimbursement_id)
    if item.requester_id != user.id:
        raise HTTPException(404, "Solicitação não encontrada.")
    if item.status != ReimbursementStatus.DRAFT:
        raise HTTPException(409, "Somente solicitações em rascunho podem ser alteradas.")
    changes = data.model_dump(exclude_unset=True)
    if "expense_date" in changes and changes["expense_date"] and changes["expense_date"] > date.today():
        raise HTTPException(422, "A data da despesa não pode ser futura.")
    if "receipt_reference" in changes and changes["receipt_reference"]:
        changes["receipt_reference"] = changes["receipt_reference"].strip()
        duplicate = db.query(Reimbursement).filter(
            Reimbursement.requester_id == user.id,
            Reimbursement.receipt_reference == changes["receipt_reference"],
            Reimbursement.id != item.id).first()
        if duplicate:
            raise HTTPException(409, "Referência de comprovante já utilizada.")
    for key, value in changes.items():
        if value is not None:
            setattr(item, key, value.strip() if isinstance(value, str) else value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Violação de integridade ao atualizar a solicitação.")
    db.refresh(item)
    return item

@app.delete("/reimbursements/{reimbursement_id}", status_code=204, tags=["Reembolsos"])
def delete_reimbursement(reimbursement_id: int, db: Session = Depends(get_db),
                         user: User = Depends(require_roles(Role.COLLABORATOR))):
    item = get_reimbursement_or_404(db, reimbursement_id)
    if item.requester_id != user.id:
        raise HTTPException(404, "Solicitação não encontrada.")
    if item.status != ReimbursementStatus.DRAFT:
        raise HTTPException(409, "Somente solicitações em rascunho podem ser excluídas.")
    db.delete(item)
    db.commit()

@app.post("/reimbursements/{reimbursement_id}/submit", response_model=ReimbursementOut, tags=["Fluxo de aprovação"])
def submit_reimbursement(reimbursement_id: int, db: Session = Depends(get_db),
                         user: User = Depends(require_roles(Role.COLLABORATOR))):
    item = get_reimbursement_or_404(db, reimbursement_id)
    if item.requester_id != user.id:
        raise HTTPException(404, "Solicitação não encontrada.")
    if item.status != ReimbursementStatus.DRAFT:
        raise HTTPException(409, "Somente rascunhos podem ser encaminhados.")
    item.status = ReimbursementStatus.WAITING_MANAGER
    add_history(db, item.id, user.id, "SUBMISSAO", "ENVIADA", "Solicitação encaminhada ao gestor.")
    db.commit()
    db.refresh(item)
    return item

@app.post("/reimbursements/{reimbursement_id}/manager-decision", response_model=ReimbursementOut, tags=["Fluxo de aprovação"])
def manager_decision(reimbursement_id: int, data: DecisionInput, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(Role.MANAGER))):
    item = get_reimbursement_or_404(db, reimbursement_id)
    if item.requester.department_id != user.department_id:
        raise HTTPException(403, "Gestor não pode analisar solicitações de outro departamento.")
    if item.requester_id == user.id:
        raise HTTPException(403, "Nenhum usuário pode aprovar solicitação de sua própria autoria.")
    if item.status != ReimbursementStatus.WAITING_MANAGER:
        raise HTTPException(409, "A solicitação não está aguardando decisão do gestor.")
    decision = (data.observation or "").strip()
    if not decision:
        raise HTTPException(422, "Informe uma justificativa/observação para a decisão.")
    if decision.upper().startswith("APROVAR:"):
        item.status = ReimbursementStatus.WAITING_FINANCE
        result = "APROVADA"
    elif decision.upper().startswith("RECUSAR:"):
        item.status = ReimbursementStatus.REJECTED
        result = "RECUSADA"
    else:
        raise HTTPException(422, "A observação deve começar com 'APROVAR:' ou 'RECUSAR:'.")
    add_history(db, item.id, user.id, "GESTOR", result, decision)
    db.commit()
    db.refresh(item)
    return item

@app.post("/reimbursements/{reimbursement_id}/finance-decision", response_model=ReimbursementOut, tags=["Fluxo de aprovação"])
def finance_decision(reimbursement_id: int, data: DecisionInput, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(Role.FINANCE))):
    item = get_reimbursement_or_404(db, reimbursement_id)
    if item.requester_id == user.id:
        raise HTTPException(403, "Nenhum usuário pode aprovar solicitação de sua própria autoria.")
    if item.status != ReimbursementStatus.WAITING_FINANCE:
        raise HTTPException(409, "A solicitação ainda não foi aprovada pelo gestor.")
    decision = (data.observation or "").strip()
    if not decision:
        raise HTTPException(422, "Informe uma justificativa/observação para a decisão.")
    if decision.upper().startswith("APROVAR:"):
        item.status = ReimbursementStatus.APPROVED
        result = "APROVADA"
    elif decision.upper().startswith("RECUSAR:"):
        item.status = ReimbursementStatus.REJECTED
        result = "RECUSADA"
    else:
        raise HTTPException(422, "A observação deve começar com 'APROVAR:' ou 'RECUSAR:'.")
    add_history(db, item.id, user.id, "FINANCEIRO", result, decision)
    db.commit()
    db.refresh(item)
    return item

@app.post("/reimbursements/{reimbursement_id}/payment", response_model=ReimbursementOut, tags=["Fluxo de aprovação"])
def register_payment(reimbursement_id: int, data: DecisionInput, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(Role.FINANCE))):
    item = get_reimbursement_or_404(db, reimbursement_id)
    if item.status != ReimbursementStatus.APPROVED:
        raise HTTPException(409, "Somente solicitações aprovadas pelo financeiro podem ser marcadas como pagas.")
    item.status = ReimbursementStatus.PAID
    observation = (data.observation or "Pagamento registrado.").strip()
    add_history(db, item.id, user.id, "PAGAMENTO", "PAGA", observation)
    db.commit()
    db.refresh(item)
    return item

@app.get("/reimbursements/{reimbursement_id}/history", response_model=list[HistoryOut], tags=["Auditoria"])
def reimbursement_history(reimbursement_id: int, db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    item = get_reimbursement_or_404(db, reimbursement_id)
    ensure_visible(item, user)
    if user.role == Role.FINANCE and item.status == ReimbursementStatus.DRAFT:
        raise HTTPException(404, "Solicitação não encontrada.")
    return item.history
