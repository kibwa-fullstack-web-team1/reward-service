import os

class Config:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-northeast-2")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "your-reward-bucket")
    KAFKA_BROKER_URL: str = os.getenv("KAFKA_BROKER_URL", "localhost:9092")
    REWARD_GENERATION_REQUESTS_TOPIC: str = os.getenv("REWARD_GENERATION_REQUESTS_TOPIC", "reward-generation-requests")
