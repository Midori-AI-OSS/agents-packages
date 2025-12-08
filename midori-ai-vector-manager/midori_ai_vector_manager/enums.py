"""Enums for vector storage."""

from enum import Enum


class SenderType(str, Enum):
    """Who sent the content - enables reranking of user content."""

    USER = "user"
    MODEL = "model"
    SYSTEM = "system"
