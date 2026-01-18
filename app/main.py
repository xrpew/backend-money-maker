from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models
from .database import SessionLocal, create_engine, get_db, engine
from pydantic import BaseModel

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"status": "Backend Operativo"}

# 1. Iniciar Partida (Gastar Token)
@app.post("/games/start")
def start_game(user_id: str, db: Session = Depends(get_db)):
    token_record = db.query(models.Token).filter(models.Token.user_id == user_id).first()
    
    if not token_record or token_record.balance <= 0:
        raise HTTPException(status_code=402, detail="Sin tokens disponibles")
    
    # Restar token
    token_record.balance -= 1
    db.commit()
    return {"status": "success", "remaining_tokens": token_record.balance}

# 2. Registrar Pago y Aumentar Pote
@app.post("/payments/confirm")
def confirm_payment(user_id: str, amount: float, db: Session = Depends(get_db)):
    # 1. Registrar el pago
    new_payment = models.Payment(user_id=user_id, amount=amount, tokens_granted=1)
    db.add(new_payment)
    
    # 2. Sumar token al usuario
    token_record = db.query(models.Token).filter(models.Token.user_id == user_id).first()
    token_record.balance += 1
    
    # 3. Aumentar el Pote (Ejemplo: 75% va al pote)
    pool = db.query(models.VaultPool).first()
    pool.total_amount += (amount * 0.75)
    
    db.commit()
    return {"new_balance": token_record.balance, "new_pool": pool.total_amount}

# 3. Obtener el Pote Actual (Público)
@app.get("/vault/pool")
def get_pool(db: Session = Depends(get_db)):
    pool = db.query(models.VaultPool).first()
    return {"total": pool.total_amount}

class UserRegisterScore(BaseModel):
    user_id: str
    email: str or None = None
    score: int
    is_vault_run: bool

def new_uuid():
    import uuid
    return str(uuid.uuid4())

# 4. Registrar Partida (Con Ticket)
@app.post("/api/scores")
# los parametros vienen en un DATA JSON, no en la query string
def register_game(data_user: UserRegisterScore, db: Session = Depends(get_db)):
    # Verificar si el usuario tiene tokens disponibles
    request_data = {"user_id": data_user.user_id, "score": data_user.score, "is_vault_run": data_user.is_vault_run}
    print(f"Registro de partida: {request_data}")
    user = db.query(models.User).filter(models.User.id == data_user.user_id).first()
    if not user:
        db.add(models.User(id=data_user.user_id, email=data_user.email or new_uuid(), username=""))
        db.commit()

    token_record = db.query(models.Token).filter(models.Token.user_id == data_user.user_id).first()
    
    if not token_record or token_record.balance <= 0:
        # Si no hay tokens, no puede registrar la partida CON EL IS_VAULT_RUN = FALSE
        is_vault_run = False
    else:
        is_vault_run = data_user.is_vault_run

    # Registrar la partida
    new_game = models.Game(user_id=data_user.user_id, score=data_user.score, is_vault_run=is_vault_run)
    db.add(new_game)
    db.commit()

    # Restar token si se usó un ticket
    if is_vault_run and token_record:
        token_record.balance -= 1
        return {"status": "success", "remaining_tokens": token_record.balance}
    else:
        return {"status": "failed", "reason": "No tokens available for vault run"}