from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.db import Base

class PersonalizationReward(Base):
    __tablename__ = "personalization_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True) # 개인화 보상은 특정 사용자에게 귀속
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    generation_prompt = Column(Text, nullable=True) # AI 생성 프롬프트
    generated_image_url = Column(String, nullable=True) # AI 생성 이미지 URL
    position_x = Column(Integer, nullable=True) # 정원 내 배치 X 좌표
    position_y = Column(Integer, nullable=True) # 정원 내 배치 Y 좌표
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
