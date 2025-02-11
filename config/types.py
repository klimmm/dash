from typing import (
     Any,
     Callable,
     Dict,
     List,
     NotRequired,
     Optional,
     TypedDict,
     Union
)

from core.lines.tree import Tree


class ButtonConfig(TypedDict):
    label: str
    value: Union[str, int]
    hidden: NotRequired[bool]


class ButtonGroupConfig(TypedDict, total=False):
    buttons: List[ButtonConfig]
    multi_select: bool
    class_key: str
    default: Union[Union[str, int], List[Union[str, int]]]
    output_transforms: List[Callable[[Union[str, int]], str]]


class DropdownConfig(TypedDict, total=False):
    id: str
    className: str
    clearable: bool
    disabled: bool
    multi: bool
    optionHeight: int
    options: List[Dict[str, Any]]
    placeholder: Union[str, List[Any]]
    searchable: bool
    style: Optional[Dict[str, Any]]
    value: Any


class DropdownConfigs(TypedDict):
    defaults: DropdownConfig
    components: Dict[str, DropdownConfig]


class TreeConfig(TypedDict):
    placeholder: str
    is_open: bool
    states: Dict[str, bool]
    selected: List[str]


class TreeDropdownConfig(TypedDict):
    config: TreeConfig
    tree: Callable[..., Tree]