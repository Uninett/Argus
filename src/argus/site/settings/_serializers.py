from typing import Optional, List, Dict

from pydantic import BaseModel, Field, RootModel


class AppUrlSetting(BaseModel):
    path: str = Field(default="")
    urlpatterns_module: str = Field(repr=False)
    namespace: Optional[str] = Field(default="", repr=False)


class AppSetting(BaseModel):
    app_name: str
    urls: Optional[AppUrlSetting] = None
    context_processors: Optional[List[str]] = None
    middleware: Optional[Dict[str, str]] = None


class ListAppSetting(RootModel):
    root: List[AppSetting]
