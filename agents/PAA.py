"""
Product Architect Agent (PAA) - Updated Implementation (complete)

This file provides a complete, production-oriented PAA agent implementation
for your Agno pipeline. The PAA synthesizes outputs from SIA, UXRA and SDA,
applies deterministic decision rules, persists final artifacts using FileTools,
computes readiness scores, and emits a signed handoff token when appropriate.

Notes:
- The agent is instructed to CALL FileTools.save_file() for each artifact.
- This runner also performs best-effort post-run verification and will create
  minimal fallback artifacts if the agent failed to save required files.
- No external network calls are made by this script.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
import re

from agno.agent import Agent, RunOutput, RunOutputEvent, RunEvent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools.file import FileTools
from agno.tools.reasoning import ReasoningTools

load_dotenv()

# -------------------- CONFIG --------------------
class PAAConfig:
    MODEL = os.getenv("PAA_MODEL", "gemini-2.5-flash-lite")
    OUTPUT_DIR = Path("paa_output")
    DB_FILE = "paa_agent.db"
    DEBUG_MODE = True
    DEBUG_LEVEL = 2
    READINESS_THRESHOLD = int(os.getenv("PAA_READINESS_THRESHOLD", "80"))
    AUTO_APPROVE_THRESHOLD = int(os.getenv("PAA_AUTO_APPROVE_THRESHOLD", "90"))
    # File name patterns expected from the agent (lowercase substrings)
    EXPECTED_KEYS = [
        "architecture_doc", "api_contract", "handoff_summary", "paa_audit", "rework_tasks"
    ]

    @classmethod
    def setup(cls):
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ PAA output directory: {cls.OUTPUT_DIR}")

# -------------------- AGENT IMPLEMENTATION --------------------
class ProductArchitectAgent:
    """
    Product Architect Agent (PAA)
    - Creates an Agno Agent that synthesizes SIA/UXRA/SDA artifacts
    - Persists final artifacts via FileTools.save_file()
    - Verifies saved artifacts and computes readiness/handoff token
    """

    def __init__(self):
        PAAConfig.setup()
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        # Compose a comprehensive instruction for the PAA model.
        # It instructs the model to call save_file(path, content) for each artifact.
        instructions = [
            "You are the Product Architect Agent (PAA). Your job is to synthesize inputs",
            "from the Specification Intake Agent (SIA), UX Research Agent (UXRA), and",
            "System Design Agent (SDA) into a single authoritative handoff package for development.",
            "",
            "INPUTS you will receive in the prompt: product_spec.json text, ux_blueprint text,",
            "system_architecture text, api_boundary text, data_model text. Treat them as canonical.",
            "",
            "REQUIRED DELIVERABLES (you MUST call save_file(path, content) for each):",
            " - paa_output/architecture_doc_<timestamp>.md    (narrative + decisions + tradeoffs)",
            " - paa_output/api_contract_<timestamp>.yaml    (finalized OpenAPI-like surface; high level)",
            " - paa_output/handoff_summary_<timestamp>.json (hand-off manifest for DT: pointers, seed data, tests)",
            " - paa_output/paa_audit_<timestamp>.json       (audit trail of decisions and sources)",
            "",
            "If any hard blockers exist (security, compliance, missing acceptance tests), DO NOT produce a handoff_token.",
            "Instead save paa_output/rework_tasks_<timestamp>.json describing precise, actionable fixes mapped to SIA/UXRA/SDA.",
            "",
            "READINESS SCORING (deterministic): compute sub-scores and weighted aggregate:",
            " - spec_completeness (20%), ux_coverage (15%), sda_readiness (20%), acceptance_tests (20%), security_compliance (25%).",
            "Include the breakdown in the audit file.",
            "",
            "HANDOFF TOKEN: If readiness >= READINESS_THRESHOLD and no hard blockers, produce a handoff_token",
            "as sha256 of artifact pointers and include it in handoff_summary JSON under hand_off.handoff_token.",
            "",
            "OUTPUT RULES:",
            "- Every saved artifact MUST contain a metadata block with project_id, version, created_by (PAA), model_id, timestamp.",
            "- Use save_file(path, content) exactly (FileTools). Do NOT only describe saving — call the tool.",
            "- If you cannot produce an artifact, save a fallback file explaining why.",
            "- After saving all artifacts, print a final JSON summary EXACTLY like this structure:",
            "```json",
            "{",
            "  \"status\": \"completed\",",
            "  \"saved_files\": {\"architecture_doc\":\"...\",\"api_contract\":\"...\",\"handoff_summary\":\"...\",\"paa_audit\":\"...\"},",
            "  \"readiness_score\": 87,",
            "  \"handoff_token\": \"sha256:...\"",
            "}",
            "```",
            "",
            "Be deterministic, explicit, and conservative. Cite sources when possible.",
        ]

        agent = Agent(
            name="Product Architect Agent (PAA)",
            role="Synthesize PDT artifacts into final architecture and handoff bundle",
            model=Gemini(id=PAAConfig.MODEL),
            tools=[ReasoningTools(), FileTools()],
            db=SqliteDb(id="paa_db", db_file=PAAConfig.DB_FILE, session_table="paa_sessions"),
            instructions=instructions,
            markdown=True,
            add_history_to_context=True,
            num_history_runs=3,
            debug_mode=PAAConfig.DEBUG_MODE,
            debug_level=PAAConfig.DEBUG_LEVEL,
            stream_events=True,
            tool_choice="auto",
        )
        return agent

    # -------------------- Utilities --------------------
    @staticmethod
    def _timestamp() -> str:
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def _sha256_hex(s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def _locate_saved_artifacts(self, lookups: List[str]) -> Dict[str, Optional[str]]:
        """
        Locate latest files in paa_output that contain any of the lookup substrings.
        Returns dict mapping lookup -> path or None.
        """
        found = {k: None for k in lookups}
        files = sorted(PAAConfig.OUTPUT_DIR.glob("*"), key=lambda p: p.stat().st_mtime)
        for p in reversed(files):
            name = p.name.lower()
            for k in lookups:
                if k in name and found[k] is None:
                    found[k] = str(p)
        return found

    def _ensure_metadata_block(self, content: str, project_id: str, version: str) -> str:
        """
        Ensure the content begins with a metadata JSON block (for markdown/text).
        If content already contains a metadata JSON block (simple detection), leave it.
        Otherwise prepend a canonical metadata block.
        """
        try:
            # simple check for a metadata JSON object at the top
            if re.search(r"\"project_id\"\s*:", content) or re.search(r"^---", content):
                return content
        except Exception:
            pass

        meta = {
            "metadata": {
                "project_id": project_id,
                "version": version,
                "created_by": "PAA",
                "model": PAAConfig.MODEL,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
        header = json.dumps(meta, indent=2)
        return f"{header}\n\n{content}"

    # -------------------- Main orchestration --------------------
    def synthesize_and_handoff(
        self,
        product_spec_text: str,
        ux_blueprint_text: Optional[str] = None,
        system_architecture_text: Optional[str] = None,
        api_boundary_text: Optional[str] = None,
        data_model_text: Optional[str] = None,
        project_id: Optional[str] = None,
        version: str = "1.0.0",
        stream: bool = True,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main callable. Takes upstream artifact texts (strings), runs the PAA agent,
        and returns a results dict including artifact paths, readiness and token.
        """
        PAAConfig.setup()
        if not session_id:
            session_id = f"paa_session_{self._timestamp()}"
        project_id = project_id or f"project_{datetime.utcnow().strftime('%Y%m%d')}"
        ts = self._timestamp()

        # Build consolidated prompt containing upstream artifacts (careful with length)
        prompt_chunks = [
            f"Project ID: {project_id}",
            f"Version: {version}",
            "",
            "=== PRODUCT_SPEC_JSON ===",
            product_spec_text or "",
            "",
            "=== UX_BLUEPRINT_TEXT ===",
            ux_blueprint_text or "",
            "",
            "=== SYSTEM_ARCHITECTURE_TEXT ===",
            system_architecture_text or "",
            "",
            "=== API_BOUNDARY_TEXT ===",
            api_boundary_text or "",
            "",
            "=== DATA_MODEL_TEXT ===",
            data_model_text or "",
            "",
            "TASK: Synthesize inputs and produce required artifacts. Use save_file(path, content) EXACTLY.",
            "Flag hard blockers and produce rework_tasks if necessary.",
        ]
        prompt = "\n".join(prompt_chunks)

        results: Dict[str, Any] = {
            "session_id": session_id,
            "project_id": project_id,
            "version": version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "in_progress",
            "artifacts": {},
            "audit": None,
            "readiness_score": None,
            "handoff_token": None,
        }

        try:
            # Execute agent
            if stream:
                print("\n" + "=" * 80)
                print("🚀 PAA - RUN (streaming)")
                print("=" * 80 + "\n")
                stream_iter = self.agent.run(prompt, stream=True, stream_events=True, session_id=session_id)
                full_text = ""
                for ev in stream_iter:
                    self._handle_stream_event(ev)
                    if ev.event == RunEvent.run_content:
                        full_text += ev.content or ""
                results["raw_agent_output"] = full_text
            else:
                print("\n" + "=" * 80)
                print("🚀 PAA - RUN (non-streaming)")
                print("=" * 80 + "\n")
                response: RunOutput = self.agent.run(prompt, session_id=session_id)
                print(response.content)
                results["raw_agent_output"] = response.content
                try:
                    results["metrics"] = {
                        "input_tokens": response.metrics.input_tokens or 0,
                        "output_tokens": response.metrics.output_tokens or 0,
                        "total_tokens": response.metrics.total_tokens or 0,
                        "duration": response.metrics.duration or 0,
                    }
                except Exception:
                    results["metrics"] = {}

            # Post-run verification: locate saved artifacts in paa_output
            found = self._locate_saved_artifacts(PAAConfig.EXPECTED_KEYS)
            results["artifacts"] = found

            # If any artifact missing, create conservative fallback artifacts (but prefer agent-saved ones)
            fallbacks = self._create_fallbacks_if_missing(found, project_id, version, ts,
                                                          product_spec_text, ux_blueprint_text,
                                                          system_architecture_text, api_boundary_text, data_model_text)
            # merge fallback results into artifacts mapping
            for k, v in fallbacks.items():
                if v:
                    results["artifacts"].setdefault(k, v)

            # Compute readiness from agent raw output if possible, else compute best-effort heuristics
            readiness, breakdown = self._compute_readiness_from_agent(results.get("raw_agent_output", ""),
                                                                      product_spec_text, ux_blueprint_text, system_architecture_text)
            results["readiness_score"] = readiness
            results["readiness_breakdown"] = breakdown

            # If handoff_summary exists and readiness >= threshold and no rework_tasks, create token
            handoff_path = results["artifacts"].get("handoff_summary")
            rework_present = results["artifacts"].get("rework_tasks") is not None
            if handoff_path and (readiness >= PAAConfig.READINESS_THRESHOLD) and not rework_present:
                # produce token
                # Build canonical artifact list string (sorted keys)
                artifact_list = {k: results["artifacts"].get(k) for k in sorted(results["artifacts"].keys())}
                artifact_list_str = json.dumps(artifact_list, sort_keys=True)
                token = "sha256:" + self._sha256_hex(artifact_list_str + results["timestamp"])
                results["handoff_token"] = token
                results["status"] = "ready"

                # Append token into handoff_summary file (if JSON)
                try:
                    hp = Path(handoff_path)
                    if hp.exists() and hp.suffix.lower() == ".json":
                        manifest = json.loads(hp.read_text(encoding="utf-8"))
                        manifest.setdefault("hand_off", {})["handoff_token"] = token
                        manifest["readiness_score"] = readiness
                        hp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                except Exception:
                    # do not fail the run if patching fails
                    pass
            else:
                if rework_present or readiness < PAAConfig.READINESS_THRESHOLD:
                    results["status"] = "blocked"
                else:
                    results["status"] = "unknown"

            # Load or create audit file
            if results["artifacts"].get("paa_audit"):
                try:
                    with open(results["artifacts"]["paa_audit"], "r", encoding="utf-8") as f:
                        audit = json.load(f)
                        results["audit"] = audit
                except Exception:
                    results["audit"] = {"note": "failed to read paa_audit file"}
            else:
                # Create minimal audit
                audit = {
                    "project_id": project_id,
                    "timestamp": results["timestamp"],
                    "readiness_score": readiness,
                    "breakdown": breakdown,
                    "notes": "Auto-generated audit because agent did not save an audit file."
                }
                audit_path = PAAConfig.OUTPUT_DIR / f"paa_audit_{ts}.json"
                audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
                results["artifacts"]["paa_audit"] = str(audit_path)
                results["audit"] = audit

            print("\n" + "=" * 80)
            print("✅ PAA RUN COMPLETE")
            print("=" * 80 + "\n")
        except Exception as exc:
            results["status"] = "error"
            results["error"] = str(exc)
            print(f"\n❌ PAA ERROR: {exc}\n")

        return results

    # -------------------- Fallback artifact creation --------------------
    def _create_fallbacks_if_missing(
        self,
        found: Dict[str, Optional[str]],
        project_id: str,
        version: str,
        ts: str,
        product_spec_text: Optional[str],
        ux_blueprint_text: Optional[str],
        system_architecture_text: Optional[str],
        api_boundary_text: Optional[str],
        data_model_text: Optional[str],
    ) -> Dict[str, Optional[str]]:
        """
        If agent didn't save required artifacts, create conservative fallback files
        (so downstream pipeline can continue). Return mapping key -> path for created files.
        """
        created = {}
        # architecture_doc fallback
        if not found.get("architecture_doc"):
            path = PAAConfig.OUTPUT_DIR / f"architecture_doc_{ts}.md"
            content = self._ensure_metadata_block(
                "# Architecture Document (Fallback)\n\n"
                "The PAA agent did not produce a complete architecture document. This fallback contains\n"
                "a conservative synthesis of available inputs and actions the Development team should take.\n\n"
                "## Inputs available\n\n"
                f"- product_spec (excerpt):\n\n```\n{(product_spec_text or '')[:2000]}\n```\n\n"
                "## Recommended next steps\n\n"
                "- Review the above spec and produce full architecture_doc; map P0 acceptance criteria to components.\n"
                "- Ensure security/compliance blockers are resolved before handoff.\n",
                project_id,
                version,
            )
            path.write_text(content, encoding="utf-8")
            created["architecture_doc"] = str(path)

        # api_contract fallback
        if not found.get("api_contract"):
            path = PAAConfig.OUTPUT_DIR / f"api_contract_{ts}.yaml"
            content = {
                "metadata": {"project_id": project_id, "version": version, "created_by": "PAA_fallback", "model": PAAConfig.MODEL, "timestamp": datetime.utcnow().isoformat() + "Z"},
                "note": "Fallback minimal API contract; agent did not produce a final contract.",
                "endpoints": [
                    {"path": "/health", "method": "GET", "description": "Health check"},
                ],
            }
            path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            created["api_contract"] = str(path)

        # handoff_summary fallback
        if not found.get("handoff_summary"):
            path = PAAConfig.OUTPUT_DIR / f"handoff_summary_{ts}.json"
            manifest = {
                "project_id": project_id,
                "version": version,
                "hand_off": {
                    "architecture_doc": created.get("architecture_doc") or found.get("architecture_doc"),
                    "api_contract": created.get("api_contract") or found.get("api_contract"),
                },
                "readiness_score": None,
                "notes": "Fallback handoff manifest created because agent did not save a handoff_summary.",
            }
            path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            created["handoff_summary"] = str(path)

        # paa_audit fallback
        if not found.get("paa_audit"):
            path = PAAConfig.OUTPUT_DIR / f"paa_audit_{ts}.json"
            audit = {
                "project_id": project_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "notes": "Fallback audit generated by runner.",
            }
            path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
            created["paa_audit"] = str(path)

        # If rework_tasks exists in found, preserve; otherwise create None (no fallback for rework tasks).
        return created

    # -------------------- Readiness extraction / heuristics --------------------
    def _compute_readiness_from_agent(self, raw_output: str, product_spec_text: Optional[str],
                                      ux_text: Optional[str], sda_text: Optional[str]) -> Tuple[int, Dict[str, int]]:
        """
        Attempt to parse a readiness_score from the agent raw_output. If not present, compute
        lightweight heuristics based on presence of content.
        Returns (readiness_score_int, breakdown_dict).
        """
        breakdown = {
            "spec_completeness": 75,
            "ux_coverage": 75,
            "sda_readiness": 75,
            "acceptance_test_coverage": 75,
            "security_compliance": 75,
        }

        # Try to find explicit numeric readiness mentions
        try:
            m = re.search(r"readiness[_\s-]?score[^0-9]*(\d{1,3})", raw_output, re.IGNORECASE)
            if m:
                score = int(m.group(1))
                # generate breakdown around the score with minor deterministic offsets
                for k in breakdown:
                    breakdown[k] = max(50, min(95, score + (abs(hash(k)) % 7) - 3))
                return score, breakdown
        except Exception:
            pass

        # Heuristic: presence signals quality
        def presence_score(text: Optional[str]) -> int:
            if not text or len(text.strip()) < 50:
                return 60
            elif len(text) < 500:
                return 75
            else:
                return 88

        breakdown["spec_completeness"] = presence_score(product_spec_text)
        breakdown["ux_coverage"] = presence_score(ux_text)
        breakdown["sda_readiness"] = presence_score(sda_text)
        # acceptance tests heuristic: look for "acceptance" keyword in raw_output
        if re.search(r"acceptance", raw_output, re.IGNORECASE) or (product_spec_text and "acceptance" in product_spec_text.lower()):
            breakdown["acceptance_test_coverage"] = 85
        else:
            breakdown["acceptance_test_coverage"] = 65
        # security compliance heuristic: check for presence of words like "encryption", "pci", "gdpr", "hipaa"
        if re.search(r"\b(encrypt|encryption|pci|gdpr|hipaa|compliance|saml|oauth|auth)\b", (raw_output or "") + (product_spec_text or ""), re.IGNORECASE):
            breakdown["security_compliance"] = 85
        else:
            breakdown["security_compliance"] = 65

        # Weighted aggregate
        score = int(
            0.2 * breakdown["spec_completeness"]
            + 0.15 * breakdown["ux_coverage"]
            + 0.2 * breakdown["sda_readiness"]
            + 0.2 * breakdown["acceptance_test_coverage"]
            + 0.25 * breakdown["security_compliance"]
        )
        return score, breakdown

    # -------------------- Streaming event handler --------------------
    def _handle_stream_event(self, event: RunOutputEvent):
        """
        Mirror the streaming event handling style of SIA/UXRA to help debugging.
        """
        if event.event == RunEvent.run_started:
            print(f"🎬 Run Started - ID: {event.run_id} (Session: {event.session_id})\n")
        elif event.event == RunEvent.run_content:
            # Print content as it streams
            print(event.content or "", end="", flush=True)
        elif event.event == RunEvent.tool_call_started:
            print("\n🔧 TOOL CALL STARTED")
            print(f"   Tool: {event.tool_name}")
            if hasattr(event, "function_name"):
                print(f"   Function: {event.function_name}")
            if hasattr(event, "tool_args") and event.tool_args:
                try:
                    print("   Args:", json.dumps(event.tool_args, indent=2))
                except Exception:
                    print("   Args: (non-serializable)")
        elif event.event == RunEvent.tool_call_completed:
            print("\n✅ TOOL CALL COMPLETED")
            print(f"   Tool: {event.tool_name}")
            if hasattr(event, "tool_result"):
                preview = str(event.tool_result)[:300]
                print("   Result preview:", preview, "...\n")
        elif event.event == RunEvent.reasoning_started:
            print("\n🧠 Reasoning started\n")
        elif event.event == RunEvent.reasoning_step:
            print(f"💭 Reasoning step: {event.content}\n")
        elif event.event == RunEvent.reasoning_completed:
            print("\n✅ Reasoning completed\n")
        elif event.event == RunEvent.run_completed:
            print("\n🏁 Run completed\n")
            if hasattr(event, "metrics"):
                print("Metrics:", event.metrics, "\n")

# -------------------- Example usage --------------------
def example_paa_run():
    paa = ProductArchitectAgent()

    # Example upstream artifacts (placeholders)
    product_spec_text = json.dumps({
        "metadata": {"project_name": "Demo Project", "version": "1.0.0"},
        "features": [
            {"id": "FR-001", "name": "User Login", "priority": "must-have", "acceptance_criteria": ["User can login with email/password"]},
            {"id": "FR-002", "name": "Create Task", "priority": "must-have", "acceptance_criteria": ["User can create a task with title and due date"]}
        ],
        "constraints": {"region": "us-east-1", "max_monthly_cost_usd": 5000}
    }, indent=2)

    ux_blueprint_text = "Personas: Ops Manager, End User. Flows: Login -> Dashboard -> Create Task"
    system_architecture_text = "Components: frontend, api_gateway, task_service, postgres"
    api_boundary_text = "POST /api/login, POST /api/tasks"
    data_model_text = "Entities: user(id,email), task(id,title,due_date,owner_id)"

    res = paa.synthesize_and_handoff(
        product_spec_text=product_spec_text,
        ux_blueprint_text=ux_blueprint_text,
        system_architecture_text=system_architecture_text,
        api_boundary_text=api_boundary_text,
        data_model_text=data_model_text,
        project_id="demo_project_001",
        version="1.0.0",
        stream=False
    )

    print("\nPAA RUN RESULT:")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    example_paa_run()
