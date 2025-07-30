from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.kafka_producer_service import get_kafka_producer, produce_reward_generation_request
from app.utils.db import get_db
from app.core import crud_service
from app import schemas # schemas 모듈 임포트 추가
from app.schemas.reward_schema import UserReward, RewardCreate # RewardCreate 스키마 임포트 추가
from app.models.reward import RewardType

router = APIRouter()

@router.post("/users/{user_id}/rewards/{reward_id}/award", response_model=UserReward)
def award_reward_to_user(user_id: int, reward_id: int, db: Session = Depends(get_db)):
    db_reward = crud_service.get_reward(db, reward_id=reward_id)
    if not db_reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    # 이미 생성된 보상을 사용자에게 지급 (성장형 또는 AI 생성 완료된 개인화 보상)
    return crud_service.create_user_reward(db=db, user_reward=schemas.UserRewardCreate(user_id=user_id, reward_id=reward_id))


@router.post("/rewards/request-ai-generation")
def request_ai_reward_generation(
    user_id: int = Body(...),
    reward_type_id: int = Body(...), # AI로 생성할 보상 유형의 ID (예: '기억의 정원 오브제'의 ID)
    generation_prompt: str = Body(...),
    db: Session = Depends(get_db)
):
    db_reward_type = crud_service.get_reward(db, reward_id=reward_type_id)
    if not db_reward_type:
        raise HTTPException(status_code=404, detail="Reward type not found")

    if db_reward_type.reward_type != RewardType.personalization:
        raise HTTPException(status_code=400, detail="Only personalization type rewards can be requested for AI generation.")

    producer = get_kafka_producer()
    produce_reward_generation_request(
        producer=producer,
        user_id=user_id,
        reward_type_id=reward_type_id,
        generation_prompt=generation_prompt
    )
    return {"message": "AI reward generation request accepted"}