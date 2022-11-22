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
            {
                "fields": ["last_invoked"],
                "expireAfterSeconds": 7776000,
            },  # 3 month after last_invoked
        ],
    }

    @staticmethod
    def get(telegram_id: str = None) -> User:
        return User.objects(telegram_id=telegram_id).first()

    def update(self):
        self.last_invoked = datetime.utcnow
        self.save()


class Secret(mongoengine.Document):
    identity = mongoengine.StringField(required=True)
    secret = mongoengine.StringField(required=True)
    chat_id = mongoengine.StringField(required=True)
    user = mongoengine.ReferenceField(User, reverse_delete_rule=mongoengine.CASCADE)
    repository = mongoengine.StringField(default="None", required=False)
    created = mongoengine.DateTimeField(default=datetime.utcnow)
    last_invoked = mongoengine.DateTimeField(default=datetime.utcnow)

    meta = {
        "db_alias": "core",
        "collections": "secrets",
        "indexes": [
            {"fields": ["identity"]},
            {
                "fields": ["last_invoked"],
                "expireAfterSeconds": 31536000,
            },  # one year after last_invoked
        ],
    }

    @staticmethod
    def get(identity: str = None) -> User:
        return Secret.objects(identity=identity).first()

    def update(self):
        self.last_invoked = datetime.utcnow
        self.save()
        self.user.update()


User.register_delete_rule(Secret, "secrets", mongoengine.PULL)
