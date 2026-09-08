import json

from groq import Groq

from app.core.config import settings


class GroqService:
    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured")

        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def extract_topics(self, paper_text: str) -> list[str]:
        if not paper_text.strip():
            return []

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research paper topic extraction system. "
                        "Read the research paper text and identify the main "
                        "research topics and technical areas. "
                        "Return only valid JSON with this structure: "
                        '{"topics": ["topic 1", "topic 2", "topic 3"]}. '
                        "Return between 3 and 8 concise topics. "
                        "Do not include explanations."
                    ),
                },
                {
                    "role": "user",
                    "content": paper_text,
                },
            ],
            response_format={
                "type": "json_object"
            },
        )

        content = response.choices[0].message.content

        if not content:
            return []

        data = json.loads(content)

        topics = data.get("topics", [])

        if not isinstance(topics, list):
            return []

        return [
            topic.strip()
            for topic in topics
            if isinstance(topic, str) and topic.strip()
        ]