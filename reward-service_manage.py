import uvicorn
from app import create_app

app = create_app()

if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8004, # reward-service는 8004번 포트 사용
        log_level="debug"
    )