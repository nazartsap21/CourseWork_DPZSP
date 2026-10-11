from typing import TypeVar

from flask import request
from pydantic import BaseModel
from werkzeug.exceptions import BadRequest

ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_body(model: type[ModelT]) -> ModelT:
    """Validates the JSON body; pydantic errors become 422 in the error handler."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequest("Request body must be a JSON object.")
    return model.model_validate(payload)
