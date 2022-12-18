# pylint: disable=wrong-import-position, unused-import, missing-module-docstring, import-error
import os
import mongoengine


def global_init():
    host = os.environ.get("MONGO_SERVER", "127.0.0.1")
    port = os.environ.get("MONGODB_PORT", "27017")
    user = os.environ.get("MONGO_USERNAME", None)
    passw = os.environ.get("MONGO_PASSWORD", None)
    db_name = os.environ.get("MONGO_INITDB_DATABASE", "test")
    mongoengine.register_connection(
        alias="core",
        db=db_name,
        username=user,
        password=passw,
        host=f"mongodb://{host}:{port}",
    )
