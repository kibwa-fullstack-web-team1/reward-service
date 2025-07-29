# reward-service

'기억의 정원' 프로젝트의 AI 생성 2D 리워드 보상 서비스를 관리합니다.

## 실행 방법

1.  **의존성 설치**
    ```bash
    pip install -r requirements.txt
    ```
2.  **환경 변수 설정**
    `.env` 파일에 데이터베이스 연결 정보 등을 설정합니다.
    ```
    DATABASE_URL="postgresql://user:password@host:port/dbname"
    # 기타 필요한 환경 변수
    ```
3.  **애플리케이션 실행**
    ```bash
    python reward-service_manage.py
    ```

## API 문서

애플리케이션 실행 후 다음 URL에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다:

`http://localhost:8004/docs`