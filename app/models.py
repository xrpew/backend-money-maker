from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # ID de Supabase Auth (UUID)
    email = Column(String, unique=True, index=True)
    username = Column(String)
    
    # Relaciones
    tokens = relationship("Token", back_populates="owner", uselist=False)
    games = relationship("Game", back_populates="player")

class Token(Base):
    __tablename__ = "tokens"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    balance = Column(Integer, default=0)
    
    owner = relationship("User", back_populates="tokens")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    amount = Column(Numeric(precision=10, scale=2))
    tokens_granted = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    score = Column(Integer)
    is_vault_run = Column(Boolean, default=False) # True si usó un ticket
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    player = relationship("User", back_populates="games")

class VaultPool(Base):
    __tablename__ = "vault_pool"
    id = Column(Integer, primary_key=True, default=1)
    total_amount = Column(Numeric(precision=10, scale=2), default=0.00)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())