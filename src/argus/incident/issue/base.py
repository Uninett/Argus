from __future__ import annotations

from abc import ABC, abstractmethod

__all__ = ["IssuePlugin"]


class IssuePlugin(ABC):
    @classmethod
    @abstractmethod
    def generate_issue_url(incident):
        return None
