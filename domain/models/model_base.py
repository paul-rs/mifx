from abc import ABC
import json
from datetime import datetime, date
from decimal import Decimal


def json_handler(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, ModelBase):
        return v.to_json()
    raise TypeError(
        f"JSON Handler Failed on value '{v}': Unknown type '{type(v)}'")


def to_json(dict_to_convert):
    return json.loads(
        json.dumps(
            dict_to_convert,
            ensure_ascii=False, default=json_handler, indent=4,
            separators=(',', ': ')
        )
    )


class ModelBase(ABC):

    def to_json_string(self):
        my_dict = {k.lstrip('_'): v for k, v in vars(self).items()}
        return json.dumps(my_dict, indent=4, default=json_handler)

    def to_json(self):
        return json.loads(self.to_json_string())

    def __eq__(self, other):
        if not isinstance(other, ModelBase):
            return False

        return self.to_json() == other.to_json()

    def __hash__(self):
        output = []
        for (k, v) in self.to_json().items():
            output_value = hash(tuple(sorted(v))) if isinstance(v, dict) else v
            output.append((k, output_value))
        return hash(tuple(sorted(output)))
