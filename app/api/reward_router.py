
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.kafka_producer_service import get_kafka_producer, produce_reward_generation_request
from app.utils.db import get_db
from app.core import crud_service
from app import schemas # schemas 모듈 임포트 추가
from app.schemas.reward_schema import UserReward, RewardCreate, UserRewardCreate # UserRewardCreate 스키마 임포트 추가
from app.models.reward import RewardType

router = APIRouter()

@router.post("/users/{user_id}/rewards/{reward_id}/award", response_model=UserReward)
def award_reward_to_user(user_id: int, reward_id: int, db: Session = Depends(get_db)):
    db_reward = crud_service.get_reward(db, reward_id=reward_id)
    if not db_reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    # 이미 생성된 보상을 사용자에게 지급 (성장형 또는 AI 생성 완료된 개인화 보상)
    return crud_service.create_user_reward(db=db, user_reward=schemas.UserRewardCreate(user_id=user_id, reward_id=reward_id))


@router.post("/rewards/request-ai-generation", response_model=UserReward) # UserReward를 반환하도록 변경
def request_ai_reward_generation(
    user_id: int = Body(...),
    reward_type_id: int = Body(...), # AI로 생성할 보상 유형의 ID (예: '기억의 정원 오브제'의 ID)
    generation_prompt: str = Body(...),
    db: Session = Depends(get_db)
):
    db_reward_type = crud_service.get_reward(db, reward_type_id)
    if not db_reward_type:
        raise HTTPException(status_code=404, detail="Reward type not found")

    if db_reward_type.reward_type != RewardType.personalization:
        raise HTTPException(status_code=400, detail="Only personalization type rewards can be requested for AI generation.")

    # 1. UserReward 레코드 조회 또는 생성
    # 이미 해당 user_id와 reward_type_id로 UserReward가 있는지 확인
    existing_user_reward = crud_service.get_user_reward_by_user_id_and_reward_id(db, user_id, reward_type_id)

    if existing_user_reward:
        # 이미 UserReward가 존재하면, generated_image_url이 없는 경우에만 요청을 진행
        if existing_user_reward.generated_image_url:
            raise HTTPException(status_code=400, detail="AI reward already generated for this user and reward type.")
        created_user_reward = existing_user_reward
    else:
        # UserReward가 없으면 새로 생성
        user_reward_data = UserRewardCreate(
            user_id=user_id,
            reward_id=reward_type_id, # 여기서는 Reward 유형 ID를 사용
            position_x=None,
            position_y=None,
            generated_image_url=None # 초기에는 이미지 URL 없음
        )
        created_user_reward = crud_service.create_user_reward(db, user_reward_data)

    # 2. Kafka 메시지에 created_user_reward.id 포함하여 발행
    producer = get_kafka_producer()
    produce_reward_generation_request(
        producer=producer,
        user_id=user_id,
        reward_type_id=reward_type_id,
        generation_prompt=generation_prompt,
        user_reward_id=created_user_reward.id # 새로 생성된 UserReward의 ID 포함
    )
    
    # 생성 또는 조회된 UserReward 객체를 반환
    return created_user_reward
