from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class CandidateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    extraction_status: str
    created_at: datetime


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_type: str
    original_filename: Optional[str] = None
    uploaded_at: datetime


class DocumentRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient: str
    subject: Optional[str] = None
    message: str
    status: str
    provider_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime


class CandidateDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    skills: Optional[List[str]] = None
    confidence: Optional[Dict[str, float]] = None
    extraction_status: str
    extraction_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    documents: List[DocumentOut] = []
    requests: List[DocumentRequestOut] = []


class ExtractedFields(BaseModel):
    """What the LLM is asked to return for a resume."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    skills: List[str] = []
    confidence: Dict[str, float] = {}
