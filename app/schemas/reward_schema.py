from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

# CommonReward 스키마
class CommonRewardBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    acquisition_condition: Optional[str] = None
    stage: Optional[int] = None
    service_category_id: Optional[int] = None

class CommonRewardCreate(CommonRewardBase):
    pass

class CommonReward(CommonRewardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# PersonalizationReward 스키마
class PersonalizationRewardBase(BaseModel):
    user_id: int
    name: str
    description: Optional[str] = None
    generation_prompt: Optional[str] = None
    generated_image_url: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None

class PersonalizationRewardCreate(PersonalizationRewardBase):
    pass

class PersonalizationReward(PersonalizationRewardBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# UserCommonReward 스키마
class UserCommonRewardBase(BaseModel):
    user_id: int
    common_reward_id: int
    position_x: Optional[int] = None
    position_y: Optional[int] = None

class UserCommonRewardCreate(UserCommonRewardBase):
    pass

class UserCommonReward(UserCommonRewardBase):
    id: int
    acquired_at: datetime
    common_reward: CommonReward # CommonReward 정보 포함

    model_config = ConfigDict(from_attributes=True)