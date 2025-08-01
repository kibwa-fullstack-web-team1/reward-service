from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.kafka_producer_service import get_kafka_producer, produce_reward_generation_request
from app.utils.db import get_db
from app.core import crud_service
from app.schemas.reward_schema import (
    CommonReward, PersonalizationReward, UserCommonReward,
    CommonRewardCreate, PersonalizationRewardCreate, UserCommonRewardCreate
)

router = APIRouter()

# 공용 리워드 관련 엔드포인트
@router.post("/rewards", response_model=CommonReward)
def create_common_reward(reward: CommonRewardCreate, db: Session = Depends(get_db)):
    db_reward = crud_service.get_common_reward_by_name(db, name=reward.name)
    if db_reward:
        raise HTTPException(status_code=400, detail="Reward name already registered")
    return crud_service.create_common_reward(db=db, reward=reward)

@router.get("/rewards", response_model=List[CommonReward])
def get_common_rewards(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rewards = crud_service.get_common_rewards(db, skip=skip, limit=limit)
    return rewards

@router.get("/rewards/{reward_id}", response_model=CommonReward)
def get_common_reward(reward_id: int, db: Session = Depends(get_db)):
    db_reward = crud_service.get_common_reward(db, reward_id=reward_id)
    if db_reward is None:
        raise HTTPException(status_code=404, detail="Reward not found")
    return db_reward

# 사용자 획득 리워드 관련 엔드포인트 (공용 및 개인화 통합 조회)
@router.get("/users/{user_id}/rewards", response_model=List[dict]) # 통합된 응답을 위해 dict 반환
def get_user_rewards(user_id: int, db: Session = Depends(get_db)):
    common_rewards = crud_service.get_user_common_rewards(db, user_id=user_id)
    personalization_rewards = crud_service.get_personalization_rewards_by_user_id(db, user_id=user_id)

    # 두 리스트를 통합하고 필요한 정보만 추출하여 반환
    combined_rewards = []
    for r in common_rewards:
        combined_rewards.append({
            "id": r.id,
            "user_id": r.user_id,
            "reward_id": r.common_reward_id,
            "name": r.common_reward.name,
            "description": r.common_reward.description,
            "image_url": r.common_reward.image_url,
            "acquired_at": r.acquired_at,
            "position_x": r.position_x,
            "position_y": r.position_y,
            "type": "common"
        })
    for r in personalization_rewards:
        combined_rewards.append({
            "id": r.id,
            "user_id": r.user_id,
            "name": r.name,
            "description": r.description,
            "generation_prompt": r.generation_prompt,
            "generated_image_url": r.generated_image_url,
            "acquired_at": r.created_at, # PersonalizationReward는 created_at을 획득 시점으로 사용
            "position_x": r.position_x,
            "position_y": r.position_y,
            "type": "personalization"
        })
    return combined_rewards

# 특정 사용자 획득 공용 리워드 상세 조회
@router.get("/user-common-rewards/{user_common_reward_id}", response_model=UserCommonReward)
def get_user_common_reward(user_common_reward_id: int, db: Session = Depends(get_db)):
    db_user_common_reward = crud_service.get_user_common_reward_by_id(db, user_common_reward_id)
    if db_user_common_reward is None:
        raise HTTPException(status_code=404, detail="User common reward not found")
    return db_user_common_reward

# 사용자가 획득한 리워드의 정원 내 배치 좌표 업데이트
@router.put("/users/{user_id}/rewards/{reward_instance_id}/position", response_model=dict) # dict 반환
def update_user_reward_position(
    user_id: int,
    reward_instance_id: int, # UserCommonReward 또는 PersonalizationReward의 ID
    reward_type: str = Query(..., description="Type of reward: 'common' or 'personalization'"),
    position_x: Optional[int] = Body(None),
    position_y: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    if reward_type == "common":
        db_user_reward = crud_service.get_user_common_reward_by_id(db, reward_instance_id)
        if db_user_reward is None or db_user_reward.user_id != user_id:
            raise HTTPException(status_code=404, detail="User common reward not found or does not belong to user")
        updated_reward = crud_service.update_user_common_reward_position(
            db, reward_instance_id, position_x, position_y
        )
    elif reward_type == "personalization":
        db_user_reward = crud_service.get_personalization_reward(db, reward_instance_id)
        if db_user_reward is None or db_user_reward.user_id != user_id:
            raise HTTPException(status_code=404, detail="Personalization reward not found or does not belong to user")
        updated_reward = crud_service.update_personalization_reward_position(
            db, reward_instance_id, position_x, position_y
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid reward type. Must be 'common' or 'personalization'.")
    
    if updated_reward is None:
        raise HTTPException(status_code=500, detail="Failed to update reward position.")

    # 업데이트된 객체를 적절한 스키마로 변환하여 반환
    if reward_type == "common":
        return {
            "id": updated_reward.id,
            "user_id": updated_reward.user_id,
            "reward_id": updated_reward.common_reward_id,
            "name": updated_reward.common_reward.name,
            "description": updated_reward.common_reward.description,
            "image_url": updated_reward.common_reward.image_url,
            "acquired_at": updated_reward.acquired_at,
            "position_x": updated_reward.position_x,
            "position_y": updated_reward.position_y,
            "type": "common"
        }
    else: # personalization
        return {
            "id": updated_reward.id,
            "user_id": updated_reward.user_id,
            "name": updated_reward.name,
            "description": updated_reward.description,
            "generation_prompt": updated_reward.generation_prompt,
            "generated_image_url": updated_reward.generated_image_url,
            "acquired_at": updated_reward.created_at,
            "position_x": updated_reward.position_x,
            "position_y": updated_reward.position_y,
            "type": "personalization"
        }

# 사용자에게 공용 리워드 지급
@router.post("/users/{user_id}/common-rewards/{common_reward_id}/award", response_model=UserCommonReward)
def award_common_reward_to_user(user_id: int, common_reward_id: int, db: Session = Depends(get_db)):
    db_common_reward = crud_service.get_common_reward(db, common_reward_id)
    if not db_common_reward:
        raise HTTPException(status_code=404, detail="Common Reward not found")

    user_common_reward_data = UserCommonRewardCreate(
        user_id=user_id,
        common_reward_id=common_reward_id,
        position_x=None,
        position_y=None
    )
    return crud_service.create_user_common_reward(db=db, user_common_reward=user_common_reward_data)

# AI 개인화 리워드 생성 요청
@router.post("/rewards/request-ai-generation", response_model=PersonalizationReward)
def request_ai_reward_generation(
    user_id: int = Body(...),
    generation_prompt: str = Body(...),
    db: Session = Depends(get_db)
):
    # PersonalizationReward는 user_id와 generation_prompt로 직접 생성
    personalization_reward_data = PersonalizationRewardCreate(
        user_id=user_id,
        name="AI 생성 개인화 보상", # 기본 이름 설정
        description="AI가 생성한 개인화된 보상입니다.", # 기본 설명 설정
        generation_prompt=generation_prompt,
        generated_image_url=None, # 초기에는 이미지 URL 없음
        position_x=None,
        position_y=None
    )
    created_personalization_reward = crud_service.create_personalization_reward(db, personalization_reward_data)

    # Kafka 메시지에 생성된 PersonalizationReward의 ID 포함하여 발행
    producer = get_kafka_producer()
    produce_reward_generation_request(
        producer=producer,
        user_id=user_id,
        reward_type_id=created_personalization_reward.id, # PersonalizationReward의 ID를 reward_type_id로 전달
        generation_prompt=generation_prompt,
        user_reward_id=created_personalization_reward.id # PersonalizationReward의 ID를 user_reward_id로 전달
    )
    
    return created_personalization_reward
