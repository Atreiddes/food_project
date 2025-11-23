"""
Тест vLLM API
"""
import httpx
import asyncio

async def test_vllm_endpoint():
    """Тест vLLM совместимого эндпоинта"""
    
    url = "http://localhost:8000/api/v1/v1/chat/completions"
    
    payload = {
        "model": "mistral",
        "messages": [
            {"role": "user", "content": "Привет! Назови 3 полезных завтрака."}
        ],
        "temperature": 0.7
    }
    
    print("🧪 Тестирование vLLM API эндпоинта...")
    print(f"📡 URL: {url}")
    print(f"📦 Payload: {payload}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=120.0)
            response.raise_for_status()
            result = response.json()
            
            print("✅ Успешный ответ от API!")
            print(f"📄 Response ID: {result.get('id')}")
            print(f"🤖 Model: {result.get('model')}")
            print(f"💬 Ответ: {result['choices'][0]['message']['content']}\n")
            print("✅ Тест пройден успешно!")
            
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_vllm_endpoint())
