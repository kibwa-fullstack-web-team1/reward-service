from fastapi import FastAPI
from app.utils.db import engine, Base
from app.config.config import Config
import logging
import sys
import asyncio
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException

# 모든 모델을 임포트하여 Base.metadata에 등록 (초기에는 비어있음)
from app.models import reward, user_reward

logger = logging.getLogger(__name__)

# 로깅 설정
logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("uvicorn").propagate = False
logging.getLogger("uvicorn.access").propagate = False
logging.getLogger("uvicorn.error").propagate = False

def create_app():
    app = FastAPI()

    app.config = Config()

    # 개발 환경에서만 테이블 자동 생성 (마이그레이션 도구 사용 시 주석 처리)
    Base.metadata.create_all(bind=engine)

    # API 라우터 포함
    from app.api import reward_router
    app.include_router(reward_router.router, prefix="/api/v1", tags=["rewards"])

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application startup event triggered.")
        
        # Kafka 브로커 준비 대기 및 토픽 생성 로직
        admin_client = AdminClient({'bootstrap.servers': Config.KAFKA_BROKER_URL})
        max_retries = 60
        retry_delay = 2
        
        for i in range(max_retries):
            try:
                metadata = admin_client.list_topics(timeout=1)
                logger.info(f"Kafka brokers are ready: {metadata.brokers}")

                topics_to_create = [Config.REWARD_GENERATION_REQUESTS_TOPIC]
                existing_topics = metadata.topics
                new_topics = []
                for topic_name in topics_to_create:
                    if topic_name not in existing_topics:
                        logger.info(f"Topic '{topic_name}' not found. Creating it...")
                        new_topics.append(NewTopic(topic_name, num_partitions=1, replication_factor=1))
                    else:
                        logger.info(f"Topic '{topic_name}' already exists.")
                
                if new_topics:
                    admin_client.create_topics(new_topics)
                    logger.info(f"Topics created successfully.")

                break
            except KafkaException as e:
                logger.warning(f"Waiting for Kafka brokers to be ready... ({i+1}/{max_retries}) - {e}")
                await asyncio.sleep(retry_delay)
            except Exception as e:
                logger.error(f"An unexpected error occurred while waiting for Kafka: {e}")
                await asyncio.sleep(retry_delay)
        else:
            logger.error("Failed to connect to Kafka brokers after multiple retries. Consumer will not start.")
            return

        # AI Reward Consumer 스레드 시작
        from app.core.ai_reward_generator import start_ai_reward_consumer
        start_ai_reward_consumer()

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutdown event triggered.")
        # 컨슈머 종료 로직 (필요시 구현)
        # from app.core.ai_reward_generator import stop_ai_reward_consumer
        # stop_ai_reward_consumer()

    @app.get("/")
    def read_root():
        return {"message": "Welcome to the Reward Service"}

    return app
