"""Minh hoạ FUNCTION CALLING thuần với Google Gemini SDK.

Tool `get_weather` được định nghĩa schema thủ công VÀ thực thi ngay trong
chính file app này. Model chỉ QUYẾT ĐỊNH gọi tool nào; app mới là nơi chạy.

Cách chạy:
    pip install -r ../requirements.txt
    export GEMINI_API_KEY=...
    python weather_function_calling.py
"""

import os
import json
import httpx
from google import genai
from google.genai import types

client = genai.Client()

MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu, và đưa ra lời khuyên thực tế "
    "(ví dụ: mang ô, mặc áo mỏng, ...)."
)

# 1. App tự định nghĩa schema của tool
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(
                type=types.Type.STRING, description="Tên thành phố"
            )
        },
        required=["city"],
    ),
)

TOOLS = [types.Tool(function_declarations=[get_weather_declaration])]


# 2. App tự thực thi tool (gọi API thời tiết thật từ WeatherAPI.com)
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "68d4b33471cc461387875347262808")

def get_weather(city: str) -> str:
    """Lấy dữ liệu thời tiết thực tế của *city* từ WeatherAPI.com."""
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHERAPI_KEY,
        "q": city,
        "aqi": "no",
        "lang": "vi"
    }
    try:
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        location = data.get("location", {})

        result = {
            "thành_phố": location.get("name", city),
            "khu_vực": location.get("region"),
            "quốc_gia": location.get("country"),
            "nhiệt_độ": f"{current.get('temp_c')}°C",
            "cảm_giác_như": f"{current.get('feelslike_c')}°C",
            "thời_tiết": current.get("condition", {}).get("text"),
            "độ_ẩm": f"{current.get('humidity')}%",
            "gió": {
                "tốc_độ": f"{current.get('wind_kph')} km/h",
                "hướng": current.get("wind_dir"),
            },
            "chỉ_số_UV": current.get("uv"),
            "tầm_nhìn": f"{current.get('vis_km')} km",
            "cập_nhật_lúc": current.get("last_updated"),
        }
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "thành_phố": city,
            "lỗi": f"Không thể lấy dữ liệu thời tiết thực tế ({str(e)})"
        }, ensure_ascii=False)


def run(prompt: str) -> str:
    """Gửi *prompt* tới Gemini, tự động xử lý function calling và trả về câu trả lời cuối."""
    contents: list[types.Content] = [
        types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    ]

    # 3. Gọi model — model quyết định có gọi tool hay không
    resp = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=TOOLS,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    # 4. Vòng lặp: nếu model yêu cầu tool, app TỰ THỰC THI rồi đưa kết quả trả lại
    while resp.function_calls:
        # Thêm phản hồi của model vào lịch sử hội thoại
        contents.append(resp.candidates[0].content)

        function_responses = []
        for fc in resp.function_calls:
            print(f"  [model yêu cầu] {fc.name}({fc.args})")
            result = get_weather(**fc.args)  # <-- app chạy, không phải model
            print(f"  [app thực thi]  -> {result}")
            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name, response={"result": result}
                )
            )

        # Gửi kết quả tool trả về cho model
        contents.append(types.Content(role="user", parts=function_responses))
        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )

    # 5. Model tổng hợp câu trả lời cuối
    return resp.text


if __name__ == "__main__":
    print("🌤️ Trợ lý thời tiết Gemini Function Calling (gõ 'exit' hoặc 'quit' để thoát)\n" + "=" * 60)
    while True:
        try:
            question = input("\nNhập câu hỏi thời tiết của bạn: ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit", "q"):
                print("Tạm biệt!")
                break
            print("\n[Đang xử lý...]")
            answer = run(question)
            print(f"\nTrả lời:\n{answer}\n" + "-" * 60)
        except (KeyboardInterrupt, EOFError):
            print("\nTạm biệt!")
            break
