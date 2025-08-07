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
from app.core.aws_s3_service import S3Service
from app.core.dify_client import get_personalized_prompt_from_dify # Dify 클라이언트 임포트
from openai import OpenAI
import requests

logger = logging.getLogger(__name__)

s3_service = S3Service()

def generate_ai_image(prompt: str) -> str:
    """
    AI 이미지 생성 API를 호출하고 이미지 URL을 반환합니다.
    """
    logger.info(f"[AI Image Generation] Generating image for prompt: {prompt}")
    
    try:
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt, # Dify에서 받은 프롬프트를 그대로 사용
            size="1024x1024",
            n=1,
        )
        image_url = response.data[0].url
        logger.info(f"[AI Image Generation] DALL-E generated image URL: {image_url}")

        image_data = requests.get(image_url).content
        s3_object_name = f"ai-generated-rewards/{int(time.time())}.png"
        s3_url = s3_service.upload_file(image_data, s3_object_name, "image/png")
        
        if s3_url:
            logger.info(f"[AI Image Generation] Image uploaded to S3: {s3_url}")
            return s3_url
        else:
            logger.error("[AI Image Generation] Failed to upload image to S3. Returning DALL-E URL.")
            return image_url

    except Exception as e:
        logger.error(f"[AI Image Generation] Error generating image with DALL-E or uploading to S3: {e}", exc_info=True)
        return f"https://kibwa-17.s3.ap-southeast-1.amazonaws.com/ai-generated-rewards/error_dummy_{int(time.time())}.png"

async def _process_message(msg):
    logger.info(f"[Kafka Consumer] Attempting to process message from topic: {msg.topic()}")
    message_value = json.loads(msg.value().decode('utf-8'))
    user_id = message_value.get("user_id")
    personalization_reward_id = message_value.get("reward_type_id")

    logger.info(f"[Kafka Consumer] Received message: user_id={user_id}, personalization_reward_id={personalization_reward_id}")

    # Dify에 전달할 LLM 프롬프트 생성
    dify_llm_prompt = f"""# 역할
당신은 사용자의 기억을 아름다운 이미지로 변환하는 예술가입니다.

# 지시
주어진 컨텍스트(사용자의 기억)의 핵심 감정과 내용을 포착하여, DALL-E가 이미지를 생성할 수 있는, 영어로 된, 하나의 사물이나 매우 단순한 구성을 묘사하는 한 문장의 프롬프트를 생성해주세요. 'in pixel art style'을 포함해야 합니다.
또한, 이 이미지가 어떤 기억을 기반으로 생성되었는지 설명하는 한국어 문장을 20자 내외로 생성해주세요. **이 설명에는 컨텍스트 내의 구체적인 인물 이름, 장소, 날짜, 또는 사건의 핵심 키워드를 반드시 포함하여 개인화된 느낌을 주어야 합니다.**

# 출력 규칙
응답은 반드시 아래의 JSON 형식이어야 합니다.
{{
  "dalle_prompt": "생성된 DALL-E 프롬프트",
  "memory_description": "기억 기반 설명 텍스트"
}}"""

    # Dify를 통해 개인화된 DALL-E 프롬프트 받아오기
    dify_response_json_str = await get_personalized_prompt_from_dify(user_id, dify_llm_prompt)

    if not dify_response_json_str:
        logger.error(f"[Kafka Consumer] Failed to get personalized prompt from Dify for user {user_id}. Aborting reward generation.")
        return

    try:
        dify_response_data = json.loads(dify_response_json_str)
        personalized_dalle_prompt = dify_response_data.get("dalle_prompt")
        memory_description = dify_response_data.get("memory_description")

        if not personalized_dalle_prompt or not memory_description:
            logger.error(f"[Kafka Consumer] Dify response missing dalle_prompt or memory_description: {dify_response_json_str}")
            return

    except json.JSONDecodeError as e:
        logger.error(f"[Kafka Consumer] Failed to parse Dify response JSON: {e}. Response: {dify_response_json_str}")
        return

    # AI 이미지 생성
    generated_image_url = generate_ai_image(personalized_dalle_prompt)

    db: Session = SessionLocal()
    try:
        personalization_reward_entry = crud_service.get_personalization_reward(db, personalization_reward_id)
        if personalization_reward_entry:
            personalization_reward_entry.generated_image_url = generated_image_url
            personalization_reward_entry.generation_prompt = personalized_dalle_prompt # Dify에서 생성된 프롬프트를 DB에 저장
            personalization_reward_entry.description = memory_description # 기억 기반 설명 저장
            db.commit()
            logger.info(f"[Kafka Consumer] Updated PersonalizationReward {personalization_reward_entry.id} with generated image URL, prompt, and description.")
        else:
            logger.warning(f"[Kafka Consumer] PersonalizationReward with ID {personalization_reward_id} not found. Cannot update image URL.")

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
            msg = consumer.poll(timeout=10.0)
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
    pass
