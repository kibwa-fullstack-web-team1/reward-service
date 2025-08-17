from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import desc

from app import models, schemas
from app.models.common_reward import CommonReward
from app.models.personalization_reward import PersonalizationReward
from app.models.user_common_reward import UserCommonReward
from app.models.service_category import ServiceCategory # New import
from app.core.aws_s3_service import S3Service

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

def delete_common_rewards_by_category(db: Session, service_category_id: int) -> int:
    """
    특정 서비스 카테고리에 속한 모든 공용 보상을 DB와 S3에서 삭제합니다.
    """
    rewards_to_delete = db.query(CommonReward).filter(CommonReward.service_category_id == service_category_id).all()
    
    if not rewards_to_delete:
        return 0

    s3_service = S3Service()
    object_keys = ['/'.join(r.image_url.split('/')[3:]) for r in rewards_to_delete if r.image_url and s3_service.bucket_name in r.image_url]
    
    if object_keys:
        s3_deleted = s3_service.delete_files(object_keys)
        if not s3_deleted:
            raise Exception("Failed to delete files from S3. Aborting operation.")

    num_deleted = db.query(CommonReward).filter(CommonReward.service_category_id == service_category_id).delete(synchronize_session=False)
    db.commit()
    
    return num_deleted

# PersonalizationReward CRUD operations
def create_personalization_reward(db: Session, reward: schemas.PersonalizationRewardCreate) -> PersonalizationReward:
    db_reward = PersonalizationReward(**reward.model_dump())
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
    db_user_common_reward = UserCommonReward(**user_common_reward.model_dump())
    db.add(db_user_common_reward)
    db.commit()
    db.refresh(db_user_common_reward)
    return db_user_common_reward

def get_user_common_rewards(db: Session, user_id: int) -> List[UserCommonReward]:
    return db.query(UserCommonReward).filter(UserCommonReward.user_id == user_id).all()

def get_user_common_reward_by_id(db: Session, user_common_reward_id: int) -> Optional[UserCommonReward]:
    return db.query(UserCommonReward).filter(UserCommonReward.id == user_common_reward_id).first()

def get_user_common_reward_by_reward_id(db: Session, user_id: int, common_reward_id: int) -> Optional[UserCommonReward]:
    return db.query(UserCommonReward).filter(
        UserCommonReward.user_id == user_id,
        UserCommonReward.common_reward_id == common_reward_id
    ).first()

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

# Refactored: Award a common reward to a user if they don't already have it.
def update_user_common_reward_stage(
    db: Session, user_id: int, new_common_reward_id: int, service_category_id: int
) -> UserCommonReward:
    # service_category_id is kept for signature consistency with the router, but not used in the new logic.
    
    # Check if the user already has this specific reward
    existing_user_reward = get_user_common_reward_by_reward_id(db, user_id, new_common_reward_id)

    if existing_user_reward:
        # If reward already awarded, return the existing record
        return existing_user_reward
    else:
        # If no existing reward, create a new one
        user_common_reward_data = schemas.UserCommonRewardCreate(
            user_id=user_id,
            common_reward_id=new_common_reward_id,
            position_x=None,
            position_y=None
        )
        return create_user_common_reward(db, user_common_reward_data)