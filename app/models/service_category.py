
from sqlalchemy import Column, Integer, String
from app.utils.db import Base

class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # 예: daily-question, story-sequencing, memory-flip-card
    display_name_ko = Column(String, nullable=False) # 예: 오늘의 질문, 이야기 순서 맞추기, 카드 뒤집기
