from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas

# Reward CRUD operations
def create_reward(db: Session, reward: schemas.RewardCreate) -> models.Reward:
    db_reward = models.Reward(
        name=reward.name,
        description=reward.description,
        generation_prompt=reward.generation_prompt,
        image_url=reward.image_url,
        acquisition_condition=reward.acquisition_condition,
        reward_type=reward.reward_type,
        stage=reward.stage,
        service_category_id=reward.service_category_id
    )
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

def get_reward(db: Session, reward_id: int) -> Optional[models.Reward]:
    return db.query(models.Reward).filter(models.Reward.id == reward_id).first()

def get_reward_by_name(db: Session, name: str) -> Optional[models.Reward]:
    return db.query(models.Reward).filter(models.Reward.name == name).first()

def get_rewards(db: Session, skip: int = 0, limit: int = 100) -> List[models.Reward]:
    return db.query(models.Reward).offset(skip).limit(limit).all()

def update_reward(db: Session, reward_id: int, reward: schemas.RewardCreate) -> Optional[models.Reward]:
    db_reward = db.query(models.Reward).filter(models.Reward.id == reward_id).first()
    if db_reward:
        for key, value in reward.model_dump(exclude_unset=True).items():
            setattr(db_reward, key, value)
        db.commit()
        db.refresh(db_reward)
    return db_reward

def delete_reward(db: Session, reward_id: int) -> Optional[models.Reward]:
    db_reward = db.query(models.Reward).filter(models.Reward.id == reward_id).first()
    if db_reward:
        db.delete(db_reward)
        db.commit()
    return db_reward

# UserReward CRUD operations
def create_user_reward(db: Session, user_reward: schemas.UserRewardCreate) -> models.UserReward:
    db_user_reward = models.UserReward(
        user_id=user_reward.user_id,
        reward_id=user_reward.reward_id,
        position_x=user_reward.position_x,
        position_y=user_reward.position_y
    )
    db.add(db_user_reward)
    db.commit()
    db.refresh(db_user_reward)
    return db_user_reward

def get_user_rewards(db: Session, user_id: int) -> List[models.UserReward]:
    return db.query(models.UserReward).filter(models.UserReward.user_id == user_id).all()

def get_user_reward_by_id(db: Session, user_reward_id: int) -> Optional[models.UserReward]:
    return db.query(models.UserReward).filter(models.UserReward.id == user_reward_id).first()

def update_user_reward_position(db: Session, user_reward_id: int, position_x: Optional[int], position_y: Optional[int]) -> Optional[models.UserReward]:
    db_user_reward = db.query(models.UserReward).filter(models.UserReward.id == user_reward_id).first()
    if db_user_reward:
        db_user_reward.position_x = position_x
        db_user_reward.position_y = position_y
        db.commit()
        db.refresh(db_user_reward)
    return db_user_reward

def delete_user_reward(db: Session, user_reward_id: int) -> Optional[models.UserReward]:
    db_user_reward = db.query(models.UserReward).filter(models.UserReward.id == user_reward_id).first()
    if db_user_reward:
        db.delete(db_user_reward)
        db.commit()
    return db_user_reward
