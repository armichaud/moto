from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass
class Metadata:
    arn: str
    mesh_owner: str
    resource_owner: str
    created_at: datetime = datetime.now()
    last_updated_at: datetime = datetime.now()
    uid: str = uuid4().hex
    version: int = 1
