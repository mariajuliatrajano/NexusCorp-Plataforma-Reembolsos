from app.database import Base, engine, SessionLocal
from app.models import Department, User, Role
from app.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if not db.query(Department).filter_by(name="Administração").first():
        dept = Department(name="Administração")
        db.add(dept)
        db.commit()
        db.refresh(dept)
    else:
        dept = db.query(Department).filter_by(name="Administração").first()
    if not db.query(User).filter_by(email="admin@nexuscorp.local").first():
        admin = User(name="Administrador", email="admin@nexuscorp.local",
                     password_hash=hash_password("TroqueEstaSenha123!"),
                     role=Role.ADMIN, department_id=dept.id)
        db.add(admin)
        db.commit()
    print("Administrador inicial: admin@nexuscorp.local")
    print("Senha inicial: TroqueEstaSenha123! (altere após entrar)")
finally:
    db.close()
