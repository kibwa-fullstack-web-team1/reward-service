from sqlalchemy import Column, Integer, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.utils.db import Base

class UserCommonReward(Base):
    __tablename__ = "user_common_rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    common_reward_id = Column(Integer, ForeignKey("common_rewards.id"), nullable=False)
    acquired_at = Column(DateTime, server_default=func.now())
    position_x = Column(Integer, nullable=True) # 정원 내 배치 X 좌표
    position_y = Column(Integer, nullable=True) # 정원 내 배치 Y 좌표

    common_reward = relationship("CommonReward")
