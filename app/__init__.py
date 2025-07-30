from fastapi import FastAPI
from app.utils.db import engine, Base
from app.config.config import Config

# 모든 모델을 임포트하여 Base.metadata에 등록 (초기에는 비어있음)
from app.models import reward, user_reward

def create_app():
    app = FastAPI()

    app.config = Config()

    # 개발 환경에서만 테이블 자동 생성 (마이그레이션 도구 사용 시 주석 처리)
    Base.metadata.create_all(bind=engine)

    # API 라우터 포함
    from app.api import reward_router
    app.include_router(reward_router.router, prefix="/api/v1", tags=["rewards"])

    @app.get("/")
    def read_root():
        return {"message": "Welcome to the Reward Service"}

    return app
