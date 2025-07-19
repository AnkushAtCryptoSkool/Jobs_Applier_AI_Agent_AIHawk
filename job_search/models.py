from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

class Job(BaseModel):
    title: str
    company: str
    description: str
    location: str
    posting_date: datetime
    apply_url: HttpUrl
    source: str = Field(..., description="Job board/source name")
    email: Optional[str] = None
    extra: Optional[dict] = None
