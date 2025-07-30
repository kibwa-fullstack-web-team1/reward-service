import json
from confluent_kafka import Producer
from app.config.config import Config

def get_kafka_producer():
    return Producer({'bootstrap.servers': Config.KAFKA_BROKER_URL})

def produce_reward_generation_request(producer: Producer, user_id: int, reward_type_id: int, generation_prompt: str):
    topic = "reward-generation-requests"
    message = {
        "user_id": user_id,
        "reward_type_id": reward_type_id,
        "generation_prompt": generation_prompt,
    }
    producer.produce(topic, key=str(user_id), value=json.dumps(message))
    producer.flush()