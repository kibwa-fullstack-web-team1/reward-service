from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# RewardType Enum을 Pydantic에서 사용하기 위해 임포트
from app.models.reward import RewardType

class RewardBase(BaseModel):
    name: str
    description: Optional[str] = None
    generation_prompt: Optional[str] = None
    image_url: Optional[str] = None
    acquisition_condition: Optional[str] = None
    reward_type: RewardType
    stage: Optional[int] = None # 성장형 보상의 단계

class RewardCreate(RewardBase):
    pass

class Reward(RewardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserRewardBase(BaseModel):
    user_id: int
    reward_id: int
    position_x: Optional[int] = None
    position_y: Optional[int] = None

class UserRewardCreate(UserRewardBase):
    pass

class UserReward(UserRewardBase):
    id: int
    acquired_at: datetime
    
    # UserReward 조회 시 Reward 정보도 함께 반환하기 위함
    reward: Reward

    model_config = ConfigDict(from_attributes=True)
