"""OneBot 事件模型搜索树。

FrontMatter:
    sidebar_position: 1
    description: onebot.collator 模块
"""

from typing_extensions import get_origin
from typing import Any, Union, Generic, TypeVar, Optional

from pygtrie import StringTrie
from nonebot.utils import logger_wrapper
from nonebot.compat import ModelField, model_fields
from nonebot.typing import origin_is_literal, all_literal_values

from nonebot.adapters import Event

E = TypeVar("E", bound=Event)
SEPARATOR = "/"


class Collator(Generic[E]):
    def __init__(
        self,
        name: str,
        models: list[type[E]],
        keys: tuple[Union[str, tuple[str, ...]], ...],
    ):
        self.name = name
        self.logger = logger_wrapper(self.name)

        self.models = models
        self.keys = keys

        self.tree = StringTrie(separator=SEPARATOR)
        self._refresh_tree()

    def add_model(self, *model: type[E]):
        self.models.extend(model)
        self._refresh_tree()

    def get_model(self, data: dict[str, Any]) -> list[type[E]]:
        key = self._key_from_dict(data)
        return [model.value for model in self.tree.prefixes(key)][::-1]

    def _refresh_tree(self):
        self.tree.clear()
        for model in self.models:
            key = self._key_from_model(model)
            if key in self.tree:
                self.logger(
                    "DEBUG",
                    f'Model for key "{key}" {self.tree[key]} is overridden by {model}',
                )
            self.tree[key] = model

    def _key_from_dict(self, data: dict[str, Any]) -> str:
        keys: list[Optional[str]] = []
        for key in self.keys:
            if isinstance(key, tuple):
                fields = list(filter(None, (data.get(k, None) for k in key)))
                if len(fields) > 1:
                    raise ValueError(f"Invalid data with incorrect fields: {fields}")
                field = fields[0] if fields else None
            else:
                field = data.get(key)
            keys.append(field)
        return self._generate_key(keys)

    def _key_from_model(self, model: type[E]) -> str:
        keys: list[Optional[str]] = []
        for key in self.keys:
            if isinstance(key, tuple):
                fields = list(
                    filter(None, (self._get_model_field(model, k) for k in key))
                )
                if len(fields) > 1:
                    raise ValueError(f"Invalid model with incorrect fields: {fields}")
                field = fields[0] if fields else None
            else:
                field = self._get_model_field(model, key)
            keys.append(field and self._get_literal_field_default(field))
        return self._generate_key(keys)

    def _generate_key(self, keys: list[Optional[str]]) -> str:
        if not self._check_key_list(keys):
            raise ValueError(
                "Invalid model with incorrect prefix "
                f"keys: {dict(zip(self.keys, keys))}"
            )
        tree_keys = ["", *list(filter(None, keys))]
        return SEPARATOR.join(tree_keys)

    def _check_key_list(self, keys: list[Optional[str]]) -> bool:
        truthy = tuple(map(bool, keys))
        return all(truthy) or not any(truthy[truthy.index(False) :])

    def _get_model_field(self, model: type[E], field: str) -> Optional[ModelField]:
        return next((f for f in model_fields(model) if f.name == field), None)

    def _get_literal_field_default(self, field: ModelField) -> Optional[str]:
        if not origin_is_literal(get_origin(field.annotation)):
            return
        allowed_values = all_literal_values(field.annotation)
        if len(allowed_values) > 1:
            return
        return allowed_values[0]
