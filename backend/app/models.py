from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship

from .database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    skills = Column(JSON, nullable=True)

    # confidence per field, e.g. {"email": 0.95, "phone": 0.8, ...}
    confidence = Column(JSON, nullable=True)

    resume_path = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=True)

    # pending | processing | done | failed
    extraction_status = Column(String(20), default="pending", nullable=False)
    extraction_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="candidate", cascade="all, delete-orphan")
    requests = relationship("DocumentRequest", back_populates="candidate", cascade="all, delete-orphan")


class DocumentRequest(Base):
    __tablename__ = "document_requests"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="logged")  # logged | sent | send_failed
    provider_id = Column(String(255), nullable=True)  # message id from Resend
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="requests")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=False)
    doc_type = Column(String(20), nullable=False)  # pan | aadhaar
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    candidate = relationship("Candidate", back_populates="documents")
