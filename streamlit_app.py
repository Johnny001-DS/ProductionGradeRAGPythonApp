import asyncio
from pathlib import Path
import time

import streamlit as st
import inngest
from dotenv import load_dotenv
import os
import requests
from rag_evaluator import evaluate_query, generate_evaluation_report

load_dotenv()

st.set_page_config(page_title="RAG Ingest PDF", page_icon="📄", layout="centered")


@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app", is_production=False)


def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path


async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )


st.title("Upload a PDF to Ingest")
uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)

if uploaded is not None:
    with st.spinner("Uploading and triggering ingestion..."):
        path = save_uploaded_pdf(uploaded)
        # Kick off the event and block until the send completes
        asyncio.run(send_rag_ingest_event(path))
        # Small pause for user feedback continuity
        time.sleep(0.3)
    st.success(f"Triggered ingestion for: {path.name}")
    st.caption("You can upload another PDF if you like.")

st.divider()
st.title("Ask a question about your PDFs")


async def send_rag_query_event(question: str, top_k: int) -> None:
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={
                "question": question,
                "top_k": top_k,
            },
        )
    )

    return result[0]


def _inngest_api_base() -> str:
    # Local dev server default; configurable via env
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")


def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])


def wait_for_run_output(event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5) -> dict:
    start = time.time()
    last_status = None
    while True:
        runs = fetch_runs(event_id)
        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status
            if status in ("Completed", "Succeeded", "Success", "Finished"):
                return run.get("output") or {}
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for run output (last status: {last_status})")
        time.sleep(poll_interval_s)


with st.form("rag_query_form"):
    question = st.text_input("Your question")
    top_k = st.number_input("How many chunks to retrieve", min_value=1, max_value=20, value=5, step=1)
    submitted = st.form_submit_button("Ask")

    if submitted and question.strip():
        with st.spinner("Sending event and generating answer..."):
            # Fire-and-forget event to Inngest for observability/workflow
            event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k)))
            # Poll the local Inngest API for the run's output
            output = wait_for_run_output(event_id)
            answer = output.get("answer", "")
            sources = output.get("sources", [])

        st.subheader("Answer")
        st.write(answer or "(No answer)")
        if sources:
            st.caption("Sources")
            for s in sources:
                st.write(f"- {s}")

        # Store query data in session for evaluation
        st.session_state.last_query = {
            "question": question.strip(),
            "answer": answer,
            "contexts": output.get("contexts", []),
            "sources": sources,
        }


# On-demand Evaluation Section
st.divider()
st.title("📊 Evaluate RAG Quality")

if "last_query" in st.session_state and st.session_state.last_query.get("answer"):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info("Evaluate the quality of the last generated answer using RAGAS metrics")
    
    with col2:
        if st.button("Evaluate Answer", key="eval_btn"):
            with st.spinner("Running RAGAS evaluation... (this may take a moment)"):
                try:
                    query_data = st.session_state.last_query
                    
                    # Run evaluation
                    metrics = evaluate_query(
                        question=query_data["question"],
                        answer=query_data["answer"],
                        contexts=query_data["contexts"],
                    )
                    
                    # Display results
                    st.success("Evaluation complete!")
                    
                    # Create columns for metric display
                    metric_cols = st.columns(4)
                    
                    metrics_dict = [
                        ("Faithfulness", metrics.faithfulness, "Is the answer factually consistent with context?"),
                        ("Answer Relevance", metrics.answer_relevance, "Does the answer address the question?"),
                        ("Context Relevance", metrics.context_relevance, "Are the contexts relevant to the question?"),
                        ("Context Recall", metrics.context_recall, "Did we retrieve all necessary information?"),
                    ]
                    
                    for idx, (col, (name, score, desc)) in enumerate(zip(metric_cols, metrics_dict)):
                        with col:
                            if score is not None:
                                # Color code based on score
                                if score > 0.8:
                                    color = "🟢"
                                elif score > 0.6:
                                    color = "🟡"
                                else:
                                    color = "🔴"
                                
                                st.metric(
                                    label=name,
                                    value=f"{score:.3f}",
                                    delta=color,
                                )
                                st.caption(desc, unsafe_allow_html=True)
                            else:
                                st.metric(label=name, value="N/A")
                    
                    # Display detailed report
                    st.subheader("📋 Detailed Report")
                    report = generate_evaluation_report(metrics)
                    st.code(report, language="text")
                    
                    # Store evaluation in session
                    st.session_state.last_evaluation = metrics
                    
                except Exception as e:
                    st.error(f"Evaluation failed: {str(e)}")
                    st.info("Make sure RAGAS and its dependencies are installed: `pip install ragas datasets`")
else:
    st.info("👆 Ask a question above first to evaluate an answer")


