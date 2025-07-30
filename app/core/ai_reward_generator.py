import json
import os
import threading
import time
import asyncio
import logging
from datetime import datetime
from confluent_kafka import Consumer, KafkaException, KafkaError
from sqlalchemy.orm import Session
from app.utils.db import SessionLocal
from app.core import crud_service
from app.config.config import Config
from app.models.reward import RewardType
from app.schemas.reward_schema import UserRewardCreate

logger = logging.getLogger(__name__)

# AI 이미지 생성 및 S3 업로드 관련 모듈 (가정)
# 실제 구현에서는 Meshy.ai 또는 다른 AI API 연동 로직이 들어갑니다。
# 여기서는 더미 함수로 대체합니다.

def generate_ai_image(prompt: str) -> str:
    """
    AI 이미지 생성 API를 호출하고 이미지 URL을 반환합니다.
    실제 구현에서는 Meshy.ai 등의 API를 사용합니다。
    """
    logger.info(f"[AI Image Generation] Generating image for prompt: {prompt}")
    # 실제 이미지 생성 및 S3 업로드 로직
    # 예시: S3에 업로드된 이미지 URL 반환
    dummy_image_url = f"https://kibwa-17.s3.ap-southeast-1.amazonaws.com/ai-generated-rewards/dummy_{int(time.time())}.png"
    logger.info(f"[AI Image Generation] Dummy image URL generated: {dummy_image_url}")
    return dummy_image_url

async def _process_message(msg):
    logger.info(f"[Kafka Consumer] Attempting to process message from topic: {msg.topic()}")
    message_value = json.loads(msg.value().decode('utf-8'))
    user_id = message_value.get("user_id")
    reward_type_id = message_value.get("reward_type_id")
    generation_prompt = message_value.get("generation_prompt")
    user_reward_id = message_value.get("user_reward_id")

    logger.info(f"[Kafka Consumer] Received message: user_id={user_id}, reward_type_id={reward_type_id}, prompt='{generation_prompt}', user_reward_id={user_reward_id}")

    # AI 이미지 생성
    generated_image_url = generate_ai_image(generation_prompt)

    db: Session = SessionLocal()
    try:
        # UserReward 레코드 조회 및 generated_image_url 업데이트
        user_reward_entry = crud_service.get_user_reward_by_id(db, user_reward_id)
        if user_reward_entry:
            user_reward_entry.generated_image_url = generated_image_url
            db.commit()
            logger.info(f"[Kafka Consumer] Updated UserReward {user_reward_entry.id} with generated image URL: {generated_image_url}")
        else:
            logger.warning(f"[Kafka Consumer] UserReward with ID {user_reward_id} not found. Cannot update image URL.")

    except Exception as e:
        db.rollback()
        logger.error(f"[Kafka Consumer] Error processing message: {e}", exc_info=True)
    finally:
        db.close()

async def _run_consumer_loop(consumer, topics, running_flag):
    logger.debug("[Kafka Consumer] _run_consumer_loop entered")
    try:
        consumer.subscribe(topics)
        logger.info(f"[Kafka Consumer] Subscribed to topics: {topics}")

        while running_flag[0]:
            msg = consumer.poll(timeout=10.0) # timeout을 10.0초로 늘림
            if msg is None:
                logger.debug("[Kafka Consumer] No message received within timeout. Continuing to poll...")
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.debug(f"[Kafka Consumer] %% {msg.topic()} [{msg.partition()}] reached end offset {msg.offset()}")
                else:
                    logger.error(f"[Kafka Consumer] Kafka consumer error: {msg.error()}", exc_info=True)
                    raise KafkaException(msg.error())
            else:
                await _process_message(msg)

    except Exception as e:
        logger.exception(f"[Kafka Consumer] Consumer loop encountered an error: {e}")
    finally:
        consumer.close()
        logger.info("[Kafka Consumer] Consumer closed.")

def start_ai_reward_consumer():
    logger.debug("[Kafka Consumer] start_ai_reward_consumer called")
    consumer_conf = {
        'bootstrap.servers': Config.KAFKA_BROKER_URL,
        'group.id': 'ai-reward-generator-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_conf)
    topic = Config.REWARD_GENERATION_REQUESTS_TOPIC

    running_flag = [True]
    consumer_thread = threading.Thread(target=lambda: asyncio.run(_run_consumer_loop(consumer, [topic], running_flag)))
    consumer_thread.daemon = True
    consumer_thread.start()
    logger.info("[Kafka Consumer] AI Reward Consumer thread started.")

def stop_ai_reward_consumer():
    # 이 함수는 현재 사용되지 않지만, 컨슈머를 안전하게 종료하기 위해 필요합니다。
    pass