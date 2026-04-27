from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LogEntry(BaseModel):
    """
    LifeOS v3.1 ?„åŸºç¤æ—¥èªŒæ¨¡?‹ã€?

    ?«æ??ªä??™å?ç«¯ç›®?æ??é?ä¾†ç?æ¬„ä? (text, date)ï¼?
    ä¹‹å??¯ä»¥?ä??§å???Prisma ??schema ?´å???
    """

    id: Optional[str] = None
    text: str
    date: datetime
