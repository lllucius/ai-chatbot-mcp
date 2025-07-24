"Pydantic schemas for base data validation."

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    "BaseSchema schema for data validation and serialization."

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="ignore",
        ser_by_alias=True,
    )


class TimestampSchema(BaseSchema):
    "TimestampSchema schema for data validation and serialization."

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if (field_name in data) and (data[field_name] is not None):
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"
        import json

        return json.dumps(data)


class UUIDSchema(BaseSchema):
    "UUIDSchema schema for data validation and serialization."

    id: Optional[uuid.UUID] = None

    def model_dump_json(self, **kwargs):
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        if ("id" in data) and (data["id"] is not None):
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])
        import json

        return json.dumps(data)


class BaseModelSchema(BaseSchema):
    "BaseModelSchema schema for data validation and serialization."

    id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def model_dump_json(self, **kwargs):
        "Model Dump Json operation."
        data = self.model_dump(**kwargs)
        if ("id" in data) and (data["id"] is not None):
            if isinstance(data["id"], uuid.UUID):
                data["id"] = str(data["id"])
        for field_name in ["created_at", "updated_at", "deleted_at"]:
            if (field_name in data) and (data[field_name] is not None):
                if isinstance(data[field_name], datetime):
                    data[field_name] = data[field_name].isoformat() + "Z"
        import json

        return json.dumps(data)
