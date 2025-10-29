"""
UX Research Agent (UXRA)
Production-capable implementation using the Agno Framework

This agent consumes a structured product specification (product_spec.json)
and produces UX artifacts: personas.json, journey_maps.yaml, wireframe_schema.json,
ux_validation.json, and ux_blueprint.md. It streams progress, writes artifacts
via FileTools, records provenance and persistence via SqliteDb, and includes
detailed instructions for deterministic behavior.
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
from agno.utils.pprint import pprint_run_response

load_dotenv()

# -------------------- CONFIGURATION --------------------
class UXRAConfig:
    MODEL = os.getenv("UXRA_MODEL", "gemini-2.5-flash-lite")
    OUTPUT_DIR = Path("uxra_output")
    DB_FILE = "uxra_agent.db"
    DEBUG_MODE = True
    DEBUG_LEVEL = 2

    @classmethod
    def setup(cls):
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ UXRA output directory: {cls.OUTPUT_DIR}")


# -------------------- UX RESEARCH AGENT --------------------
class UXResearchAgent:
    """
    UX Research Agent:
    - Input: structured spec (text or JSON) typically produced by SIA
    - Output: personas.json, journey_maps.yaml, wireframe_schema.json,
              ux_validation.json, ux_blueprint.md (all saved via FileTools)
    """

    def __init__(self):
        UXRAConfig.setup()
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """
        Create and configure the Agno Agent for UX Research.
        The instructions are deliberately prescriptive and deterministic
        so downstream agents (SDA, PAA) get high-quality artifacts.
        """
        instructions = [
    "You are the **UX Research Agent (UXRA)** — a senior-level UX strategist and researcher.",
    "",
    "Your mission: Convert a structured product specification into UX artifacts: personas, journeys, wireframes, validation, and blueprint.",
    "",
    "### 🔍 INPUT",
    "- You receive a JSON-based product specification from the Specification Intake Agent (SIA).",
    "- It contains metadata, business context, features, and user roles.",
    "",
    "### 🎯 GOALS",
    "You must **produce and SAVE** five UX artifacts based on the specification:",
    "",
    "1️⃣ `personas.json` — 3–7 detailed personas (role, goals, pain points, key tasks, success metrics).",
    "2️⃣ `journey_maps.yaml` — user journeys per persona (stages, tasks, emotions, touchpoints, metrics).",
    "3️⃣ `wireframe_schema.json` — logical structure of screens and components per flow.",
    "4️⃣ `ux_validation.json` — results of heuristic & accessibility checks, with scores.",
    "5️⃣ `ux_blueprint.md` — narrative explanation of UX rationale and principles.",
    "",
    "### 🧩 RULES FOR OUTPUT CREATION",
    "- You MUST use the `save_file(path, content)` tool to persist each file.",
    "- NEVER just describe the save. Actually CALL the tool using `save_file()`.",
    "- Save all files to the directory `uxra_output/`.",
    "- Name files using this exact pattern:",
    "  - uxra_output/personas_<timestamp>.json",
    "  - uxra_output/journey_maps_<timestamp>.yaml",
    "  - uxra_output/wireframe_schema_<timestamp>.json",
    "  - uxra_output/ux_validation_<timestamp>.json",
    "  - uxra_output/ux_blueprint_<timestamp>.md",
    "",
    "### ⚙️ CONTENT REQUIREMENTS",
    "Each saved file must include metadata:",
    "```json",
    "{",
    "  \"metadata\": {",
    "    \"project_id\": \"...\",",
    "    \"version\": \"1.0.0\",",
    "    \"created_by\": \"UXRA\",",
    "    \"model\": \"{{model_id}}\",",
    "    \"timestamp\": \"{{timestamp}}\"",
    "  }",
    "}",
    "```",
    "",
    "### 🧠 METHODOLOGY",
    "1. Analyze product spec → extract user types, roles, and flows.",
    "2. Derive personas with clear differentiation and motivations.",
    "3. Map key journeys with goals, context, and system responses.",
    "4. Create wireframe schema at conceptual level — not UI details.",
    "5. Evaluate design against Nielsen heuristics + WCAG 2.1.",
    "6. Assign heuristic_score (0.0–1.0) and accessibility_score (0.0–1.0).",
    "7. Save all outputs using FileTools.save_file() — one per file.",
    "8. Return a JSON summary listing all generated file paths and scores.",
    "",
    "### 🚨 ENFORCEMENT",
    "- If any save_file() call is missing, stop and fix it before finalizing.",
    "- Do NOT end response without confirming all five save_file calls succeeded.",
    "- If you cannot create an artifact, generate a fallback JSON with reason and still save it.",
    "",
    "### ✅ FINAL RESPONSE FORMAT",
    "1. Start with a short Markdown summary (UX insights, persona overview).",
    "2. Then sequentially call `save_file()` 5 times to write each artifact.",
    "3. Finish by printing a final JSON summary:",
    "```json",
    "{",
    "  \"status\": \"completed\",",
    "  \"saved_files\": {",
    "    \"personas\": \"<path>\",",
    "    \"journey_maps\": \"<path>\",",
    "    \"wireframe_schema\": \"<path>\",",
    "    \"ux_validation\": \"<path>\",",
    "    \"ux_blueprint\": \"<path>\"",
    "  },",
    "  \"scores\": {",
    "    \"heuristic_score\": 0.92,",
    "    \"accessibility_score\": 0.88",
    "  }",
    "}",
    "```",
    "",
    "Make sure that every save_file call is executed, not implied.",
    "Your output is used by automated pipelines, so missing files cause a hard failure."
]

        agent = Agent(
            name="UX Research Agent (UXRA)",
            role="Produce personas, journey maps, wireframes and UX validation artifacts from a structured spec",
            model=Gemini(id=UXRAConfig.MODEL),
            tools=[
                ReasoningTools(),
                FileTools()
            ],
            db=SqliteDb(
                id="uxra_db",
                db_file=UXRAConfig.DB_FILE,
                session_table="uxra_sessions"
            ),
            instructions=instructions,
            markdown=True,
            add_history_to_context=True,
            num_history_runs=3,
            debug_mode=UXRAConfig.DEBUG_MODE,
            debug_level=UXRAConfig.DEBUG_LEVEL,
            stream_events=True,
            tool_choice="auto",
        )

        return agent

    def generate_ux_artifacts(
        self,
        product_spec_text: str,
        project_id: Optional[str] = None,
        version: str = "1.0.0",
        stream: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry - given product_spec(JSON as string) produce UX artifacts.
        Returns summary dict with file paths, metrics, and readiness.
        """
        print("\n" + "=" * 80)
        print("🚀 UX RESEARCH AGENT - STARTING")
        print("=" * 80)

        if not session_id:
            session_id = f"uxra_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        timestamp = datetime.utcnow().isoformat() + "Z"
        project_id = project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Prepare prompt - be explicit about required saved files
        prompt = f"""
You are the UX Research Agent (UXRA).
You will receive a structured product specification below.

Your task:
1. Derive UX personas, journey maps, wireframe schema, validation, and UX blueprint.
2. **Save each artifact** using the save_file tool in the 'uxra_output' directory.
3. Ensure ALL 5 files are created.
4. After saving all files, return a JSON summary including file paths and scores.

Here is the input specification (from SIA):

{product_spec_text}

Follow your instructions carefully — explicitly CALL save_file() for each artifact.
Do NOT skip any. Confirm each save in your output.
"""

        # results container
        results = {
            "session_id": session_id,
            "timestamp": timestamp,
            "project_id": project_id,
            "version": version,
            "artifacts": {},
            "metrics": {},
            "status": "in_progress"
        }

        try:
            if stream:
                print("\n📊 STREAMING AGENT RESPONSE:")
                print("-" * 80 + "\n")

                stream_iter = self.agent.run(
                    prompt,
                    stream=True,
                    stream_events=True,
                    session_id=session_id
                )

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
                print(f"Respone : {response}")
                print(response.content)
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

            # After agent run, locate saved files in output dir (most recent ones)
            files = sorted(UXRAConfig.OUTPUT_DIR.glob("*"), key=lambda p: p.stat().st_mtime)
            # pick those matching the current timestamp or project_id if present
            artifact_paths = {}
            for p in files[-20:]:  # check last 20 files
                name = p.name.lower()
                if project_id.replace("project_", "") in name or True:
                    # best-effort: capture files by suffix we expect
                    if "personas" in name and name.endswith(".json"):
                        artifact_paths["personas"] = str(p)
                    if "journey" in name and p.suffix in (".yaml", ".yml", ".json"):
                        artifact_paths["journey_maps"] = str(p)
                    if "wireframe" in name and p.suffix == ".json":
                        artifact_paths["wireframe_schema"] = str(p)
                    if "ux_validation" in name and p.suffix == ".json":
                        artifact_paths["ux_validation"] = str(p)
                    if "ux_blueprint" in name and p.suffix in (".md", ".txt"):
                        artifact_paths["ux_blueprint"] = str(p)

            results["artifacts"] = artifact_paths

            print("\n" + "=" * 80)
            print("✅ UXRA RUN COMPLETE")
            print("=" * 80 + "\n")

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            print(f"\n❌ ERROR during UXRA run: {e}\n")

        return results

    def _handle_stream_event(self, event: RunOutputEvent):
        """
        Handle streaming events to provide visibility similar to SIA.
        """
        if event.event == RunEvent.run_started:
            print(f"🎬 Run Started - ID: {event.run_id} (Session: {event.session_id})\n")

        elif event.event == RunEvent.run_content:
            # Streamed textual content from the agent
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
                print("   Result preview:", str(event.tool_result)[:300], "...\n")

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
        Simple interactive CLI to paste a product_spec JSON and invoke the agent.
        """
        print("\n=== UX Research Agent - Interactive Mode ===\n")
        print("Paste your product_spec JSON and end with an empty line (or type 'exit').\n")

        buffer_lines = []
        while True:
            line = input()
            if line.strip().lower() in ("exit", "quit"):
                break
            if line.strip() == "":
                if buffer_lines:
                    spec_text = "\n".join(buffer_lines)
                    print("\nRunning UXRA on provided spec...\n")
                    res = self.generate_ux_artifacts(spec_text, stream=True)
                    print(json.dumps(res, indent=2))
                    buffer_lines = []
                    print("\nYou can paste another spec or type 'exit' to quit.\n")
                else:
                    continue
            else:
                buffer_lines.append(line)


# -------------------- USAGE EXAMPLES --------------------
def example_run_from_file(spec_path: str):
    """
    Load a product_spec.json file from disk and run the UXRA agent.
    """
    uxra = UXResearchAgent()

    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()

    result = uxra.generate_ux_artifacts(spec_text, stream=True)
    print("\n=== RESULT SUMMARY ===")
    print(json.dumps(result, indent=2))


def example_simple_inline():
    """
    Inline spec example for quick testing.
    """
    uxra = UXResearchAgent()

    # Minimal sample spec (stringified JSON)
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
            "accessibility": {"wcag": "2.1 AA"}
        }
    }, indent=2)

    res = uxra.generate_ux_artifacts(sample_spec, project_id="sample_proj_001", stream=False)
    print("\n=== RESULT SUMMARY ===")
    print(json.dumps(res))


# -------------------- MAIN --------------------
if __name__ == "__main__":
    # Example: run quick inline test
    example_simple_inline()

    # Example using file
    # example_run_from_file("sia_output/task_spec_20251027_123456.json")

    # Example interactive CLI
    # uxra = UXResearchAgent()
    # uxra.interactive_cli()
