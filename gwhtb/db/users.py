from __future__ import annotations
import mongoengine
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class User(mongoengine.Document):
    telegram_id = mongoengine.StringField(required=True)
    secrets = mongoengine.ListField(mongoengine.ReferenceField("Secret"))
    created = mongoengine.DateTimeField(default=datetime.utcnow)
    last_invoked = mongoengine.DateTimeField(default=datetime.utcnow)

    meta = {
        "db_alias": "core",
        "collections": "users",
        "indexes": [
            {"fields": ["telegram_id"]},
        ],
    }

    @staticmethod
    def get(telegram_id: str = None) -> User:
        return User.objects(telegram_id=telegram_id).first()

    def update(self):
        self.last_invoked = datetime.utcnow
        self.save()


class Secret(mongoengine.Document):
    secret = mongoengine.StringField(required=True)
    chat_id = mongoengine.StringField(required=True)
    user = mongoengine.ReferenceField(User)
    created = mongoengine.DateTimeField(default=datetime.utcnow)
    last_invoked = mongoengine.DateTimeField(default=datetime.utcnow)

    meta = {
        "db_alias": "core",
        "collections": "secrets",
        "indexes": [
            {"fields": ["secret"]},
        ],
    }

    @staticmethod
    def get(secret: str = None) -> User:
        return Secret.objects(secret=secret).first()

    def update(self):
        self.last_invoked = datetime.utcnow
        self.save()
        self.user.update()
