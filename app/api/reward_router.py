
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.kafka_producer_service import get_kafka_producer, produce_reward_generation_request
from app.utils.db import get_db
from app.core import crud_service
from app.schemas.reward_schema import UserReward
from app.models.reward import RewardType

router = APIRouter()

@router.post("/users/{user_id}/rewards/{reward_id}/award", response_model=UserReward)
def award_reward_to_user(user_id: int, reward_id: int, db: Session = Depends(get_db)):
    db_reward = crud_service.get_reward(db, reward_id=reward_id)
    if not db_reward:
        raise HTTPException(status_code=404, detail="Reward not found")

    if db_reward.reward_type == RewardType.personalization:
        producer = get_kafka_producer()
        produce_reward_generation_request(
            producer=producer,
            user_id=user_id,
            reward_type_id=db_reward.id,
            generation_prompt=db_reward.generation_prompt
        )
        return {"message": "AI reward generation request accepted"}

    return crud_service.create_user_reward(db=db, user_id=user_id, reward_id=reward_id)
