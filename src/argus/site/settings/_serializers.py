from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field, RootModel


class AppUrlSetting(BaseModel):
    path: str = Field(default="")
    urlpatterns_module: str = Field(repr=False)
    namespace: Optional[str] = Field(default="", repr=False)


class AppSetting(BaseModel):
    app_name: Optional[str] = None
    urls: Optional[AppUrlSetting] = None
    context_processors: Optional[List[str]] = None
    middleware: Optional[Dict[str, str]] = None
    settings: Optional[Dict[str, Any]] = None


class ListAppSetting(RootModel):
    root: List[AppSetting]
