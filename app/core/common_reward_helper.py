from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import UploadFile

from app.core.aws_s3_service import S3Service
from app.core import crud_service
from app.schemas.reward_schema import CommonRewardCreate, CommonReward

s3_service = S3Service()

async def upload_growth_reward_images_to_s3(
    service_category_id: int,
    images: List[UploadFile]
) -> List[str]:
    uploaded_image_urls = []
    for i, image_file in enumerate(images):
        contents = await image_file.read()
        object_name = f"common-rewards/{service_category_id}/stage_{i+1}.png"
        image_url = s3_service.upload_file(contents, object_name, image_file.content_type)
        if not image_url:
            raise HTTPException(status_code=500, detail=f"Failed to upload stage {i+1} image to S3")
        uploaded_image_urls.append(image_url)
    return uploaded_image_urls

async def create_growth_rewards_in_db(
    db: Session,
    service_category_id: int,
    service_name: str,
    uploaded_image_urls: List[str]
) -> List[CommonReward]:
    created_rewards = []
    description_templates = [
        f"{service_name} 서비스의 최초 이용 보상입니다.",
        f"{service_name} 서비스의 10회 이용 보상입니다.",
        f"{service_name} 서비스의 20회 이용 보상입니다.",
        f"{service_name} 서비스의 40회 이용 보상입니다.",
        f"{service_name} 서비스의 100회 이용 보상입니다."
    ]
    acquisition_conditions = ["1회", "10회", "20회", "40회", "100회"]

    for i in range(5):
        reward_name = f"{service_name} {i+1}단계 보상"
        reward_description = description_templates[i]
        image_url = uploaded_image_urls[i]
        stage = i + 1
        acquisition_condition_text = acquisition_conditions[i]

        common_reward_create_data = CommonRewardCreate(
            name=reward_name,
            description=reward_description,
            image_url=image_url,
            acquisition_condition=acquisition_condition_text,
            stage=stage,
            service_category_id=service_category_id
        )
        db_reward = crud_service.create_common_reward(db, common_reward_create_data)
        created_rewards.append(db_reward)
    
    return created_rewards
