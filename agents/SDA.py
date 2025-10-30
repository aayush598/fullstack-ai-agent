"""
System Design Agent (SDA)
Production-capable implementation using the Agno Framework

This agent consumes a structured product specification (product_spec.json)
and a UX blueprint (optional) and produces system design artifacts:
- system_architecture_<timestamp>.yaml
- component_list_<timestamp>.md
- data_model_summary_<timestamp>.yaml
- api_boundary_map_<timestamp>.yaml
- scalability_plan_<timestamp>.md
- resiliency_plan_<timestamp>.md
- security_surface_<timestamp>.md
- handoff_manifest_<timestamp>.json
- sda_audit_<timestamp>.json

The agent streams progress, writes artifacts via FileTools.save_file,
records provenance via SqliteDb, and emits a JSON summary on completion.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from agno.agent import Agent, RunOutput, RunOutputEvent, RunEvent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools.reasoning import ReasoningTools
from agno.tools.file import FileTools

load_dotenv()

# -------------------- CONFIGURATION --------------------
class SDAConfig:
    MODEL = os.getenv("SDA_MODEL", "gemini-2.5-flash-lite")
    OUTPUT_DIR = Path("sda_output")
    DB_FILE = "sda_agent.db"
    DEBUG_MODE = True
    DEBUG_LEVEL = 2

    @classmethod
    def setup(cls):
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ SDA output directory: {cls.OUTPUT_DIR}")

# -------------------- SYSTEM DESIGN AGENT --------------------
class SystemDesignAgent:
    """
    System Design Agent:
    - Input: structured spec (JSON string) and optionally UX blueprint text
    - Output: system architecture artifacts saved via FileTools
    """

    def __init__(self):
        SDAConfig.setup()
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """
        Create and configure the Agno Agent for System Design.
        Instructions force deterministic outputs and explicit save_file calls.
        """
        instructions = [
            "You are the **System Design Agent (SDA)** — a senior platform architect.",
            "",
            "Your mission: Convert a validated product specification and UX blueprint into a",
            "comprehensive system design package consisting of multiple artifacts.",
            "",
            "### INPUTS",
            "- You receive a structured product specification (JSON) and an optional UX blueprint.",
            "",
            "### DELIVERABLES (MUST SAVE USING save_file(path, content))",
            "Produce and SAVE the following files (in the sda_output/ directory):",
            "1) system_architecture_<timestamp>.yaml",
            "2) component_list_<timestamp>.md",
            "3) data_model_summary_<timestamp>.yaml",
            "4) api_boundary_map_<timestamp>.yaml",
            "5) scalability_plan_<timestamp>.md",
            "6) resiliency_plan_<timestamp>.md",
            "7) security_surface_<timestamp>.md",
            "8) handoff_manifest_<timestamp>.json",
            "9) sda_audit_<timestamp>.json",
            "",
            "### ARTIFACT CONTENT REQUIREMENTS",
            "- Each artifact must include a `metadata` block with: project_id, version, created_by, model, timestamp.",
            "- `system_architecture` must list components (id, name, type, responsibilities, persistence, recommended_techs),",
            "  interactions (from,to,protocol,sync_async,sla_ms_p95), and non-functional requirements.",
            "- `data_model_summary` should include entities (name, primary_key, fields with types, retention, sensitive flag).",
            "- `api_boundary_map` should include endpoint path, method, request/response schema stubs, auth_required, rate_limit.",
            "- `scalability_plan` must cover caching, partitioning, ingestion patterns, and autoscaling recommendations.",
            "- `resiliency_plan` must specify backups, RTO/RPO, multi-AZ strategies, and rollback guidance.",
            "- `security_surface` must outline trust boundaries, encryption points, IAM, and special compliance notes.",
            "- `handoff_manifest` must include artifact pointers, seed data location (or placeholders), acceptance mapping, and handoff_token.",
            "- `sda_audit` must contain the provenance of major design decisions: sources, prompts, confidence scores.",
            "",
            "### OPERATIONAL RULES",
            "- You MUST call FileTools.save_file(path, content) for each artifact; do not just describe that you saved.",
            "- If you cannot produce an artifact, save a fallback JSON or text file explaining why, and proceed.",
            "- All files must be saved under the `sda_output/` directory and named using the timestamp pattern exactly.",
            "- Include source citations for any template or pattern used (e.g., KB doc ids).",
            "",
            "### FINAL OUTPUT",
            "After saving all artifacts, print a final JSON summary with the following structure:",
            "```json",
            "{",
            "  \"status\": \"completed\",",
            "  \"saved_files\": { ... },",
            "  \"scores\": {\"feasibility_index\": 0.82, \"readiness_score\": 0.78},",
            "  \"handoff_token\": \"...\"",
            "}",
            "```",
            "",
            "Be deterministic, explicit, and conservative in your recommendations. Avoid hallucinations; cite sources when possible.",
        ]

        agent = Agent(
            name="System Design Agent (SDA)",
            role="Produce system architecture artifacts from structured spec and UX blueprint",
            model=Gemini(id=SDAConfig.MODEL),
            tools=[ReasoningTools(), FileTools()],
            db=SqliteDb(id="sda_db", db_file=SDAConfig.DB_FILE, session_table="sda_sessions"),
            instructions=instructions,
            markdown=True,
            add_history_to_context=True,
            num_history_runs=3,
            debug_mode=SDAConfig.DEBUG_MODE,
            debug_level=SDAConfig.DEBUG_LEVEL,
            stream_events=True,
            tool_choice="auto",
        )
        return agent

    def generate_system_design(
        self,
        product_spec_text: str,
        ux_blueprint_text: Optional[str] = None,
        project_id: Optional[str] = None,
        version: str = "1.0.0",
        stream: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entrypoint - generate system design artifacts from a product specification.

        Returns: dict with artifact paths, scores, audit info, and status.
        """
        print("\n" + "=" * 80)
        print("🚀 SYSTEM DESIGN AGENT - STARTING")
        print("=" * 80)

        if not session_id:
            session_id = f"sda_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ts_iso = datetime.utcnow().isoformat() + "Z"
        project_id = project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Prepare the prompt with explicit instructions and placeholders
        prompt = f"""
You are the System Design Agent (SDA). Use the product_spec and optional ux_blueprint supplied below.
You must produce and save the mandated artifacts into the sda_output/ directory using save_file(path, content).
Project metadata:
- project_id: {project_id}
- version: {version}
- timestamp: {ts_iso}

PRODUCT_SPEC:
{product_spec_text}

UX_BLUEPRINT (optional):
{ux_blueprint_text or '<none>'}

Follow your instructions exactly — call save_file() for each file.
After all saves, emit a JSON summary listing saved file paths, scores, and a handoff_token.
"""

        results: Dict[str, Any] = {
            "session_id": session_id,
            "timestamp": ts_iso,
            "project_id": project_id,
            "version": version,
            "artifacts": {},
            "scores": {},
            "audit": {},
            "status": "in_progress",
        }

        # names
        base = f"{timestamp}"
        filenames = {
            "system_architecture": f"sda_output/system_architecture_{base}.yaml",
            "component_list": f"sda_output/component_list_{base}.md",
            "data_model_summary": f"sda_output/data_model_summary_{base}.yaml",
            "api_boundary_map": f"sda_output/api_boundary_map_{base}.yaml",
            "scalability_plan": f"sda_output/scalability_plan_{base}.md",
            "resiliency_plan": f"sda_output/resiliency_plan_{base}.md",
            "security_surface": f"sda_output/security_surface_{base}.md",
            "handoff_manifest": f"sda_output/handoff_manifest_{base}.json",
            "sda_audit": f"sda_output/sda_audit_{base}.json",
        }

        try:
            if stream:
                print("\n📊 STREAMING AGENT RESPONSE:")
                print("-" * 80 + "\n")
                stream_iter = self.agent.run(prompt, stream=True, stream_events=True, session_id=session_id)

                full_content = ""
                for event in stream_iter:
                    self._handle_stream_event(event)
                    if event.event == RunEvent.run_content:
                        full_content += event.content or ""

                results["raw_content"] = full_content
                results["status"] = "completed"
            else:
                print("\n📊 AGENT PROCESSING (Non-streaming):")
                print("-" * 80 + "\n")
                response: RunOutput = self.agent.run(prompt, session_id=session_id)
                results["raw_content"] = response.content
                results["run_id"] = response.run_id
                try:
                    results["metrics"] = {
                        "input_tokens": response.metrics.input_tokens or 0,
                        "output_tokens": response.metrics.output_tokens or 0,
                        "total_tokens": response.metrics.total_tokens or 0,
                        "time_seconds": response.metrics.duration or 0,
                    }
                except Exception:
                    results["metrics"] = {}
                results["status"] = "completed"

            # After agent run, attempt to locate saved files produced by the agent.
            saved = {}
            # Look for files with current timestamp suffix; fallback to most recent matching names
            for key, path_str in filenames.items():
                p = Path(path_str)
                if p.exists():
                    saved[key] = str(p)
                else:
                    # fallback search in sda_output directory for the key
                    candidates = sorted(SDAConfig.OUTPUT_DIR.glob(f"*{key.split('_')[0]}*"), key=lambda p: p.stat().st_mtime)
                    if candidates:
                        saved[key] = str(candidates[-1])
            results["artifacts"] = saved

            # Try to load audit file if present to populate scores and audit info
            audit_path = saved.get("sda_audit")
            if audit_path:
                try:
                    with open(audit_path, "r", encoding="utf-8") as f:
                        audit = json.load(f)
                    results["audit"] = audit
                    # if audit contains scores, surface them
                    if isinstance(audit, dict):
                        if "scores" in audit:
                            results["scores"] = audit["scores"]
                except Exception:
                    pass

            # If no handoff manifest found, generate a minimal placeholder and save it
            if "handoff_manifest" not in saved or not Path(saved.get("handoff_manifest", "")).exists():
                handoff = {
                    "project_id": project_id,
                    "version": version,
                    "created_at": ts_iso,
                    "artifact_pointers": saved,
                    "notes": "Auto-generated placeholder handoff manifest. Please review artifacts.",
                    "handoff_token": f"handoff_{project_id}_{base}"
                }
                handoff_path = filenames["handoff_manifest"]
                FileTools().save_file(handoff_path, json.dumps(handoff, indent=2))
                saved["handoff_manifest"] = handoff_path
                results["artifacts"] = saved

            # Ensure there is an sda_audit file; if not create a minimal one
            if "sda_audit" not in saved or not Path(saved.get("sda_audit", "")).exists():
                audit = {
                    "project_id": project_id,
                    "version": version,
                    "created_at": ts_iso,
                    "decisions": [],
                    "scores": results.get("scores", {"feasibility_index": 0.0, "readiness_score": 0.0}),
                    "notes": "No detailed audit produced by agent. Please inspect artifacts."
                }
                audit_path = filenames["sda_audit"]
                FileTools().save_file(audit_path, json.dumps(audit, indent=2))
                saved["sda_audit"] = audit_path
                results["artifacts"] = saved
                results["audit"] = audit

            # compute a simple readiness/handoff token
            handoff_token = f"handoff_{project_id}_{base}"
            results["handoff_token"] = handoff_token
            results["status"] = "completed"

            print("\n" + "=" * 80)
            print("✅ SDA RUN COMPLETE")
            print("=" * 80 + "\n")

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            print(f"\n❌ ERROR during SDA run: {e}\n")

        return results

    def _handle_stream_event(self, event: RunOutputEvent):
        """
        Handle streaming events to provide visibility (mirrors UXRA/SIA handlers).
        """
        if event.event == RunEvent.run_started:
            print(f"🎬 Run Started - ID: {event.run_id} (Session: {event.session_id})\n")

        elif event.event == RunEvent.run_content:
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

    def interactive_cli(self):
        """
        Simple CLI: paste product_spec JSON + optional UX text, then run the agent.
        """
        print("\n=== System Design Agent - Interactive Mode ===\n")
        print("Paste your product_spec JSON (end with an empty line). Type 'exit' to quit.\n")

        buffer_lines = []
        print("Enter product spec:")
        while True:
            line = input()
            if line.strip().lower() in ("exit", "quit"):
                break
            if line.strip() == "":
                if buffer_lines:
                    spec_text = "\n".join(buffer_lines)
                    print("\nRunning SDA on provided spec...\n")
                    res = self.generate_system_design(spec_text, stream=True)
                    print(json.dumps(res, indent=2))
                    buffer_lines = []
                    print("\nYou can paste another spec or type 'exit' to quit.\n")
                else:
                    continue
            else:
                buffer_lines.append(line)

# -------------------- USAGE EXAMPLES --------------------
def example_run_from_file(spec_path: str, ux_path: Optional[str] = None):
    sda = SystemDesignAgent()
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()
    ux_text = None
    if ux_path:
        with open(ux_path, "r", encoding="utf-8") as f:
            ux_text = f.read()
    result = sda.generate_system_design(spec_text, ux_blueprint_text=ux_text, stream=True)
    print("\n=== RESULT SUMMARY ===")
    print(json.dumps(result, indent=2))

def example_simple_inline():
    sda = SystemDesignAgent()
    sample_spec = json.dumps({
        "project_meta": {
            "project_id": "sample_proj_001",
            "title": "Sample Recruitment Platform",
            "description": "Manage applications, schedule interviews, and track hires."
        },
        "features": [
            {"id": "F-001", "name": "Candidate Dashboard", "description": "View candidate status"},
            {"id": "F-002", "name": "Interview Scheduler", "description": "Schedule interviews with slots"}
        ],
        "users": [
            {"role": "Recruiter", "goals": ["Manage candidates", "Schedule interviews"]},
            {"role": "Candidate", "goals": ["Apply to jobs", "View status"]}
        ],
        "non_functional_requirements": {
            "performance": {"response_time": "500ms p95"},
            "availability": {"uptime": "99.9%"}
        }
    }, indent=2)
    res = sda.generate_system_design(sample_spec, stream=False)
    print("\n=== RESULT SUMMARY ===")
    print(json.dumps(res, indent=2))

# -------------------- MAIN --------------------
if __name__ == "__main__":
    # Quick inline test
    example_simple_inline()

    # Or load from files
    # example_run_from_file("sia_output/task_spec_20251027_123456.json", "uxra_output/ux_blueprint_20251027_123500.md")

    # Or interactive
    # sda = SystemDesignAgent()
    # sda.interactive_cli()
