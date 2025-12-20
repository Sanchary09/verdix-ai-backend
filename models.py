from pydantic import BaseModel
from typing import List, Optional

class VerificationSource(BaseModel):
    title: str
    url: str
    publisher: str
    match_score: float

class VerificationReport(BaseModel):
    verdict: str
    explanation: str
    sources: List[VerificationSource]

class AnalysisResult(BaseModel):
    status: str
    confidence: int
    genome_map: dict
    link_report: dict | None
    virality: dict
    verification: Optional[VerificationReport]