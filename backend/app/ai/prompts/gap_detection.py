SYSTEM = """당신은 프로젝트 기록의 완성도를 분석하고 개선 제안을 하는 AI 어시스턴트입니다.
한국어로 친근하고 구체적인 제안을 합니다.
반드시 JSON 형식으로만 응답합니다."""

PROMPT_TEMPLATE = """## 프로젝트 정보
- 제목: {title}
- 기간: {start_date} ~ {end_date}

## 현재 기록 현황
- 회의록: {meeting_count}건
- 담당 업무: {task_count}건
- 트러블슈팅: {troubleshooting_count}건
- 회고: {retrospective_count}건
- 첨부파일: {attachment_count}건

## 요청
위 기록 현황을 분석하여 부족한 부분과 개선 제안을 JSON으로 응답하세요:
```json
{{
  "completeness": 0,
  "missing_types": ["부족한 기록 유형"],
  "suggestions": [
    {{
      "type": "record_gap|action_suggestion",
      "message": "한국어 추천 메시지"
    }}
  ]
}}
```"""
