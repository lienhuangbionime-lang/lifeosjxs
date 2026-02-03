from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LogEntry(BaseModel):
    """
    LifeOS v3.1 的基礎日誌模型。

    暫時只保留前端目前會送過來的欄位 (text, date)，
    之後可以再依照原本 Prisma 的 schema 擴充。
    """

    id: Optional[str] = None
    text: str
    date: datetime
