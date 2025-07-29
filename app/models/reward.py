from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, Enum
from app.utils.db import Base
import enum

class RewardType(enum.Enum):
    growth = "growth"
    personalization = "personalization"

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    generation_prompt = Column(Text, nullable=True) # AI 생성 프롬프트
    image_url = Column(String, nullable=True) # AI 생성 이미지 URL
    acquisition_condition = Column(Text, nullable=True) # 획득 조건 설명
    reward_type = Column(Enum(RewardType), nullable=False) # 유형 (성장형/개인화)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
