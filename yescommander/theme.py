from typing import Any, Dict, Iterable, List, Type, TypeVar, Union, cast, no_type_check

__all__ = ["theme"]


class Theme:
    """dot.notation access to dictionary attributes"""

    def __setattr__(self, attr: str, value: Any) -> None:
        self.__dict__[attr] = value

    def __getattr__(self, attr: str) -> Any:
        return self.__dict__[attr]

    def to_dict(self) -> Dict[Any, Any]:
        ans = {}
        for k, v in self.__dict__.items():
            ans[k] = v.to_dict() if isinstance(v, Theme) else v
        return ans


theme = Theme()
theme.marker_color = ""
theme.preview = Theme()
theme.preview.bg_color = ""
theme.preview.title_color = ""
theme.preview.frame_color = "black"
theme.preview.frame = True
theme.preview.narrow_height = 8  # Used for narrow layout
theme.searchbox = Theme()
theme.searchbox.prompt = "> "
theme.default_marker = "- "
theme.listbox = Theme()
theme.listbox.ratio = 0.4
theme.listbox.highlight_color = ""
theme.listbox.bg_color = ""
theme.max_narrow_width = 80
theme.wide_height = 20
theme.narrow_height = 20
theme.highlight_color = "grey"
theme.color_depth = 24
# TODO: Add more ui size control parameters
