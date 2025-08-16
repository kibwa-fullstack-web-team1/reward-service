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
    # 1. 해당 카테고리의 모든 공용 보상 조회
    rewards_to_delete = db.query(CommonReward).filter(CommonReward.service_category_id == service_category_id).all()
    
    if not rewards_to_delete:
        return 0

    # 2. S3에서 관련 파일 삭제
    s3_service = S3Service()
    object_keys = []
    for reward in rewards_to_delete:
        if reward.image_url and s3_service.bucket_name in reward.image_url:
            # URL에서 객체 키 추출 (예: https://bucket.s3.region.amazonaws.com/key -> key)
            key = '/'.join(reward.image_url.split('/')[3:])
            object_keys.append(key)
    
    if object_keys:
        s3_deleted = s3_service.delete_files(object_keys)
        if not s3_deleted:
            # S3 삭제 실패 시, DB 삭제를 진행하지 않음
            raise Exception("Failed to delete files from S3. Aborting operation.")

    # 3. 데이터베이스에서 보상 삭제
    # UserCommonReward에서 해당 보상을 참조하는 경우를 먼저 처리해야 할 수 있음 (예: ON DELETE SET NULL)
    # 여기서는 CASCADE 설정이 되어 있다고 가정하고 진행
    num_deleted = db.query(CommonReward).filter(CommonReward.service_category_id == service_category_id).delete(synchronize_session=False)
    db.commit()
    
    return num_deleted

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

# New: Get user's highest stage common reward for a specific service
def get_user_highest_stage_common_reward_for_service(
    db: Session, user_id: int, service_category_id: int
) -> Optional[UserCommonReward]:
    return (
        db.query(models.user_common_reward.UserCommonReward)
        .join(models.common_reward.CommonReward) # Join with CommonReward to access stage
        .filter(
            models.user_common_reward.UserCommonReward.user_id == user_id,
            models.common_reward.CommonReward.service_category_id == service_category_id
        )
        .order_by(desc(models.common_reward.CommonReward.stage))
        .first()
    )

# New: Update user's common reward stage or create new
def update_user_common_reward_stage(
    db: Session, user_id: int, new_common_reward_id: int, service_category_id: int
) -> UserCommonReward:
    # Get the stage of the new common reward
    new_common_reward = get_common_reward(db, new_common_reward_id)
    if not new_common_reward:
        raise ValueError(f"Common reward with ID {new_common_reward_id} not found.")

    # Get the user's current highest stage common reward for this service
    existing_user_reward = get_user_highest_stage_common_reward_for_service(db, user_id, service_category_id)

    if existing_user_reward:
        # If new stage is higher, update the existing reward
        if new_common_reward.stage > existing_user_reward.common_reward.stage:
            existing_user_reward.common_reward_id = new_common_reward_id
            db.commit()
            db.refresh(existing_user_reward)
            return existing_user_reward
        else:
            # If new stage is not higher, return the existing one (no update needed)
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