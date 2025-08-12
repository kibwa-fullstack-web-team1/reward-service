import httpx
import json
from typing import Optional

from app.config.config import Config

DIFY_API_URL = Config.DIFY_API_URL
DIFY_WORKFLOW_ID = Config.DIFY_WORKFLOW_ID
DIFY_APP_API_KEY = Config.DIFY_APP_API_KEY

async def get_personalized_prompt_from_dify(user_id: int, llm_prompt: str) -> Optional[str]:
    """
    Dify 워크플로우를 호출하여 개인화된 DALL-E 프롬프트를 가져옵니다.
    """
    if not DIFY_API_URL or not DIFY_WORKFLOW_ID or not DIFY_APP_API_KEY:
        print("Dify API 설정이 완료되지 않았습니다.")
        return None

    # DALL-E 프롬프트를 더 명확하게 수정 (누끼 딴 것 같은 이미지 강조)
    enhanced_prompt = f"An isolated, single object, {llm_prompt}, in highly detailed 8-bit pixel art style, with a perfectly transparent background, no surrounding elements, no white or colored background."

    url = f"{DIFY_API_URL}/v1/workflows/run"
    headers = {
        "Authorization": f"Bearer {DIFY_APP_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {
            "sys_user_id": str(user_id),
            "llm_prompt": enhanced_prompt,
        },
        "response_mode": "blocking",
        "user": f"user_{user_id}"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            result = response.json()
            
            dalle_prompt = result.get("data", {}).get("outputs", {}).get("result")
            if dalle_prompt:
                print(f"Dify workflow successfully returned prompt for user {user_id}.")
                return dalle_prompt
            else:
                print(f"Dify workflow returned no prompt for user {user_id}. Response: {result}")
                return None
        except httpx.HTTPStatusError as e:
            print(f"Dify 워크플로우 호출 중 HTTP 오류 발생: {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Dify 워크플로우 연결 오류 발생: {e}")
            return None
        except Exception as e:
            print(f"Dify 워크플로우 호출 중 알 수 없는 오류 발생: {e}")
            return None
