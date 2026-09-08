import uuid

from sqlalchemy.orm import Session

from app.models.topic import Topic, PaperTopic


class TopicRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_normalized_name(self, normalized_name: str) -> Topic | None:
        return (
            self.db.query(Topic)
            .filter(Topic.normalized_name == normalized_name)
            .first()
        )

    def create(self, name: str, normalized_name: str) -> Topic:
        topic = Topic(
            name=name,
            normalized_name=normalized_name,
        )
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)
        return topic

    def add_paper_link(
        self,
        paper_id: uuid.UUID,
        topic_id: uuid.UUID,
        relevance_score: float | None = None,
    ) -> PaperTopic:
        existing = (
            self.db.query(PaperTopic)
            .filter(
                PaperTopic.paper_id == paper_id,
                PaperTopic.topic_id == topic_id,
            )
            .first()
        )

        if existing is not None:
            return existing

        link = PaperTopic(
            paper_id=paper_id,
            topic_id=topic_id,
            relevance_score=relevance_score,
        )

        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link