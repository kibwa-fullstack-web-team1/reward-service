from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.utils.db import Base

class UserReward(Base):
    __tablename__ = "user_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    acquired_at = Column(DateTime, server_default=func.now())
    position_x = Column(Integer, nullable=True) # 정원 내 배치 X 좌표
    position_y = Column(Integer, nullable=True) # 정원 내 배치 Y 좌표

    # 한 사용자는 같은 리워드를 한 번만 획득할 수 있도록 UniqueConstraint 추가
    __table_args__ = (UniqueConstraint('user_id', 'reward_id', name='_user_reward_uc'),)

    reward = relationship("Reward")
