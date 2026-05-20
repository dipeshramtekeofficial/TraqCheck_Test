import os
import time

import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8765")

st.set_page_config(page_title="TraqCheck", layout="wide")
st.title("TraqCheck")


def _raise_for_status(r):
    if r.ok:
        return
    try:
        detail = r.json().get("detail")
    except ValueError:
        detail = r.text
    if isinstance(detail, list):
        detail = "; ".join(str(d.get("msg", d)) for d in detail)
    raise RuntimeError(detail or f"Request failed: {r.status_code}")


def api_get(path):
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    _raise_for_status(r)
    return r.json()


def api_post(path, files=None, data=None):
    r = requests.post(f"{API_BASE}{path}", files=files, data=data, timeout=120)
    _raise_for_status(r)
    return r.json()


def api_delete(path):
    r = requests.delete(f"{API_BASE}{path}", timeout=30)
    if r.status_code not in (200, 204):
        _raise_for_status(r)


tab_upload, tab_list = st.tabs(["Upload Resume", "Candidates"])

with tab_upload:
    st.subheader("Upload a resume")
    resume = st.file_uploader("PDF, DOC or DOCX", type=["pdf", "doc", "docx"])
    if st.button("Upload", disabled=not resume):
        try:
            res = api_post(
                "/candidates/upload",
                files={"file": (resume.name, resume.getvalue())},
            )
            st.success(f"Uploaded. Candidate ID: {res['id']} — extraction running in background.")
        except Exception as e:
            st.error(str(e))

with tab_list:
    if st.button("Refresh"):
        st.rerun()

    try:
        candidates = api_get("/candidates")
    except Exception as e:
        st.error(f"Could not reach backend at {API_BASE}: {e}")
        candidates = []

    if any(c["extraction_status"] == "processing" for c in candidates):
        st_autorefresh(interval=2000, key="processing-poll")
        st.caption("Auto-refreshing while extraction is in progress…")

    if not candidates:
        st.info("No candidates yet. Upload a resume to get started.")

    for c in candidates:
        label = f"#{c['id']} — {c.get('name') or '(name pending)'} [{c['extraction_status']}]"
        with st.expander(label):
            try:
                detail = api_get(f"/candidates/{c['id']}")
            except Exception as e:
                st.error(str(e))
                continue

            cols = st.columns(2)
            cols[0].write(f"**Email:** {detail.get('email') or '—'}")
            cols[0].write(f"**Phone:** {detail.get('phone') or '—'}")
            cols[0].write(f"**Company:** {detail.get('company') or '—'}")
            cols[1].write(f"**Designation:** {detail.get('designation') or '—'}")
            cols[1].write(f"**Skills:** {', '.join(detail.get('skills') or []) or '—'}")
            cols[1].write(f"**Status:** {detail['extraction_status']}")

            if detail.get("extraction_error"):
                st.warning(detail["extraction_error"])

            st.markdown("**Documents**")
            docs = detail.get("documents") or []
            if not docs:
                st.caption("No documents uploaded yet.")
            for d in docs:
                dcols = st.columns([3, 1])
                dcols[0].write(f"`{d['doc_type']}` — {d.get('original_filename') or d['id']}")
                if dcols[1].button("Delete", key=f"del-{d['id']}"):
                    try:
                        api_delete(f"/candidates/{c['id']}/documents/{d['id']}")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

            st.markdown("**Upload PAN / Aadhaar**")
            ucols = st.columns(2)
            pan_file = ucols[0].file_uploader(
                "PAN (filename must contain 'pan')",
                type=["pdf", "png", "jpg", "jpeg", "webp"],
                key=f"pan-{c['id']}",
            )
            aad_file = ucols[1].file_uploader(
                "Aadhaar (filename must contain 'aadhaar' or 'aadhar')",
                type=["pdf", "png", "jpg", "jpeg", "webp"],
                key=f"aad-{c['id']}",
            )
            if st.button("Submit documents", key=f"submit-{c['id']}", disabled=not (pan_file or aad_file)):
                files = {}
                if pan_file:
                    files["pan"] = (pan_file.name, pan_file.getvalue())
                if aad_file:
                    files["aadhaar"] = (aad_file.name, aad_file.getvalue())
                try:
                    api_post(f"/candidates/{c['id']}/submit-documents", files=files)
                    st.success("Documents submitted.")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

            st.markdown("**Email candidate for documents**")
            if st.button("Send document request", key=f"req-{c['id']}", disabled=detail["extraction_status"] != "done"):
                try:
                    req = api_post(f"/candidates/{c['id']}/request-documents")
                    st.success(f"Request {req['status']} → {req['recipient']}")
                except Exception as e:
                    st.error(str(e))
