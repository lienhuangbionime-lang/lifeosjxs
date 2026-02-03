from app.models.gemini import LogAnalysisResult # 引入剛定義的模型
response = model.generate_content(
    contents=user_prompt,
    config={
        "response_mime_type": "application/json",
        # [CTO 關鍵指令] 啟用結構化思維
        "response_json_schema": LogAnalysisResult.model_json_schema(),
    },
)