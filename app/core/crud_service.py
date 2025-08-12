from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas
from app.models.common_reward import CommonReward
from app.models.personalization_reward import PersonalizationReward
from app.models.user_common_reward import UserCommonReward
from app.models.service_category import ServiceCategory # New import

# CommonReward CRUD operations
def create_common_reward(db: Session, reward: schemas.CommonRewardCreate) -> CommonReward:
    db_reward = CommonReward(
        name=reward.name,
        description=reward.description,
        image_url=reward.image_url,
        acquisition_condition=reward.acquisition_condition,
        stage=reward.stage,
        service_category_id=reward.service_category_id
    )
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

def get_common_reward(db: Session, reward_id: int) -> Optional[CommonReward]:
    return db.query(CommonReward).filter(CommonReward.id == reward_id).first()

def get_common_reward_by_name(db: Session, name: str) -> Optional[CommonReward]:
    return db.query(CommonReward).filter(CommonReward.name == name).first()

def get_common_rewards(db: Session, skip: int = 0, limit: int = 100) -> List[CommonReward]:
    return db.query(CommonReward).offset(skip).limit(limit).all()

def update_common_reward(db: Session, reward_id: int, reward: schemas.CommonRewardCreate) -> Optional[CommonReward]:
    db_reward = db.query(CommonReward).filter(CommonReward.id == reward_id).first()
    if db_reward:
        for key, value in reward.model_dump(exclude_unset=True).items():
            setattr(db_reward, key, value)
        db.commit()
        db.refresh(db_reward)
    return db_reward

def delete_common_reward(db: Session, reward_id: int) -> Optional[CommonReward]:
    db_reward = db.query(CommonReward).filter(CommonReward.id == reward_id).first()
    if db_reward:
        db.delete(db_reward)
        db.commit()
    return db_reward

# PersonalizationReward CRUD operations
def create_personalization_reward(db: Session, reward: schemas.PersonalizationRewardCreate) -> PersonalizationReward:
    db_reward = PersonalizationReward(
        user_id=reward.user_id,
        name=reward.name,
        description=reward.description,
        generation_prompt=reward.generation_prompt,
        generated_image_url=reward.generated_image_url,
        position_x=reward.position_x,
        position_y=reward.position_y
    )
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

def get_personalization_reward(db: Session, reward_id: int) -> Optional[PersonalizationReward]:
    return db.query(PersonalizationReward).filter(PersonalizationReward.id == reward_id).first()

def get_personalization_rewards_by_user_id(db: Session, user_id: int) -> List[PersonalizationReward]:
    return db.query(PersonalizationReward).filter(PersonalizationReward.user_id == user_id).all()

def update_personalization_reward_position(db: Session, reward_id: int, position_x: Optional[int], position_y: Optional[int]) -> Optional[PersonalizationReward]:
    db_reward = db.query(PersonalizationReward).filter(PersonalizationReward.id == reward_id).first()
    if db_reward:
        db_reward.position_x = position_x
        db_reward.position_y = position_y
        db.commit()
        db.refresh(db_reward)
    return db_reward

def delete_personalization_reward(db: Session, reward_id: int) -> Optional[PersonalizationReward]:
    db_reward = db.query(PersonalizationReward).filter(PersonalizationReward.id == reward_id).first()
    if db_reward:
        db.delete(db_reward)
        db.commit()
    return db_reward

# UserCommonReward CRUD operations
def create_user_common_reward(db: Session, user_common_reward: schemas.UserCommonRewardCreate) -> UserCommonReward:
    db_user_common_reward = UserCommonReward(
        user_id=user_common_reward.user_id,
        common_reward_id=user_common_reward.common_reward_id,
        position_x=user_common_reward.position_x,
        position_y=user_common_reward.position_y
    )
    db.add(db_user_common_reward)
    db.commit()
    db.refresh(db_user_common_reward)
    return db_user_common_reward

def get_user_common_rewards(db: Session, user_id: int) -> List[UserCommonReward]:
    return db.query(UserCommonReward).filter(UserCommonReward.user_id == user_id).all()

def get_user_common_reward_by_id(db: Session, user_common_reward_id: int) -> Optional[UserCommonReward]:
    return db.query(UserCommonReward).filter(UserCommonReward.id == user_common_reward_id).first()

def update_user_common_reward_position(db: Session, user_common_reward_id: int, position_x: Optional[int], position_y: Optional[int]) -> Optional[UserCommonReward]:
    db_user_common_reward = db.query(UserCommonReward).filter(UserCommonReward.id == user_common_reward_id).first()
    if db_user_common_reward:
        db_user_common_reward.position_x = position_x
        db_user_common_reward.position_y = position_y
        db.commit()
        db.refresh(db_user_common_reward)
    return db_user_common_reward

# ServiceCategory CRUD operations
def get_service_category(db: Session, service_category_id: int) -> Optional[ServiceCategory]:
    return db.query(ServiceCategory).filter(ServiceCategory.id == service_category_id).first()
