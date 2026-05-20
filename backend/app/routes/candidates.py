import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..models import Candidate, Document, DocumentRequest
from ..schemas import (
    CandidateSummary,
    CandidateDetail,
    DocumentOut,
    DocumentRequestOut,
)
from ..config import RESUME_DIR, DOCUMENT_DIR
from ..services.resume_parser import read_resume_text, extract_fields
from ..services.ai_agent import run_document_request_agent
from ..services import email_sender


router = APIRouter(prefix="/candidates", tags=["candidates"])

ALLOWED_RESUME_EXT = {"pdf", "docx", "doc"}
ALLOWED_DOC_EXT = {"pdf", "png", "jpg", "jpeg", "webp"}
MAX_RESUME_MB = 10
MAX_DOC_MB = 8

# Hints we look for in the uploaded filename per doc type. The candidate is
# expected to name files something like "pan_card.pdf" / "my_aadhaar.jpg".
DOC_NAME_HINTS = {
    "pan": ("pan",),
    "aadhaar": ("aadhar", "aadhaar"),
}


def _ext(name: str) -> str:
    return name.lower().rsplit(".", 1)[-1] if "." in name else ""


def _safe_name(original: str) -> str:
    ext = _ext(original)
    return f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex


@router.post("/upload", response_model=CandidateDetail, status_code=201)
async def upload_resume(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = _ext(file.filename)
    if ext not in ALLOWED_RESUME_EXT:
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_RESUME_EXT))}")

    contents = await file.read()
    if len(contents) > MAX_RESUME_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (>{MAX_RESUME_MB} MB)")

    stored_name = _safe_name(file.filename)
    stored_path = RESUME_DIR / stored_name
    stored_path.write_bytes(contents)

    candidate = Candidate(
        resume_path=str(stored_path),
        extraction_status="processing",
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Kick extraction off in the background so the upload feels snappy.
    background.add_task(_run_extraction, candidate.id, contents, file.filename)

    return candidate


def _run_extraction(candidate_id: int, file_bytes: bytes, filename: str):
    """Runs in a background task - opens its own DB session."""
    db = SessionLocal()
    try:
        cand = db.get(Candidate, candidate_id)
        if not cand:
            return
        try:
            text = read_resume_text(file_bytes, filename)
            cand.raw_text = text[:200_000]  # keep raw text reasonable

            fields = extract_fields(text)
            cand.name = fields.get("name")
            cand.email = fields.get("email")
            cand.phone = fields.get("phone")
            cand.company = fields.get("company")
            cand.designation = fields.get("designation")
            cand.skills = fields.get("skills") or []
            cand.confidence = fields.get("confidence") or {}

            if fields.get("_llm_error"):
                cand.extraction_status = "done"
                cand.extraction_error = f"LLM unavailable; used fallback. {fields['_llm_error']}"
            else:
                cand.extraction_status = "done"
                cand.extraction_error = None
            db.commit()
        except Exception as e:
            cand.extraction_status = "failed"
            cand.extraction_error = str(e)
            db.commit()
    finally:
        db.close()


@router.get("", response_model=List[CandidateSummary])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).order_by(Candidate.created_at.desc()).all()


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")
    return cand


@router.get("/{candidate_id}/resume")
def download_resume(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand or not cand.resume_path or not Path(cand.resume_path).exists():
        raise HTTPException(404, "Resume not found")
    return FileResponse(cand.resume_path)


@router.post("/{candidate_id}/request-documents", response_model=DocumentRequestOut, status_code=201)
def request_documents(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")
    if cand.extraction_status != "done":
        raise HTTPException(400, "Cannot request documents before extraction completes")

    if not cand.email:
        raise HTTPException(400, "Candidate has no email on file")

    candidate_dict = {
        "name": cand.name,
        "email": cand.email,
        "company": cand.company,
        "designation": cand.designation,
        "skills": cand.skills or [],
    }

    result = run_document_request_agent(candidate_dict)

    if not result.get("recipient"):
        raise HTTPException(400, "Could not determine an email recipient")

    req = DocumentRequest(
        candidate_id=cand.id,
        recipient=result["recipient"],
        subject=result.get("subject"),
        message=result["message"],
        status="logged",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    if email_sender.is_configured():
        ok, msg_id, err = email_sender.send_email(
            to=req.recipient,
            subject=req.subject or "Document request",
            body=req.message,
        )
        req.status = "sent" if ok else "send_failed"
        req.provider_id = msg_id
        req.error = err
        db.commit()
        db.refresh(req)

    return req


@router.post("/{candidate_id}/submit-documents", response_model=List[DocumentOut], status_code=201)
async def submit_documents(
    candidate_id: int,
    pan: Optional[UploadFile] = File(None),
    aadhaar: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "Candidate not found")

    if not pan and not aadhaar:
        raise HTTPException(400, "Upload at least one of: pan, aadhaar")

    saved: list[Document] = []
    for doc_type, upload in (("pan", pan), ("aadhaar", aadhaar)):
        if not upload:
            continue

        name_lower = (upload.filename or "").lower()
        if not any(hint in name_lower for hint in DOC_NAME_HINTS[doc_type]):
            raise HTTPException(
                400,
                "Is it the correct file uploaded? The file name must contain Pan and Aadhar",
            )

        ext = _ext(upload.filename or "")
        if ext not in ALLOWED_DOC_EXT:
            raise HTTPException(400, f"Unsupported {doc_type} file type")
        data = await upload.read()
        if len(data) > MAX_DOC_MB * 1024 * 1024:
            raise HTTPException(413, f"{doc_type} file too large (>{MAX_DOC_MB} MB)")

        target_dir = DOCUMENT_DIR / str(candidate_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        stored = target_dir / _safe_name(upload.filename or f"{doc_type}.bin")
        stored.write_bytes(data)

        doc = Document(
            candidate_id=candidate_id,
            doc_type=doc_type,
            file_path=str(stored),
            original_filename=upload.filename,
        )
        db.add(doc)
        saved.append(doc)

    db.commit()
    for d in saved:
        db.refresh(d)
    return saved


@router.get("/{candidate_id}/documents/{doc_id}")
def download_document(candidate_id: int, doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc or doc.candidate_id != candidate_id:
        raise HTTPException(404, "Document not found")
    if not Path(doc.file_path).exists():
        raise HTTPException(410, "Document file is missing on disk")
    return FileResponse(doc.file_path, filename=doc.original_filename or os.path.basename(doc.file_path))


@router.delete("/{candidate_id}/documents/{doc_id}", status_code=204)
def delete_document(candidate_id: int, doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc or doc.candidate_id != candidate_id:
        raise HTTPException(404, "Document not found")

    # Best-effort file cleanup; missing files shouldn't block deleting the row.
    try:
        path = Path(doc.file_path)
        if path.exists():
            path.unlink()
    except OSError:
        pass

    db.delete(doc)
    db.commit()
