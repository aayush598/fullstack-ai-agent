"""
System Design Agent (SDA) — Multi-Prompt Architecture
FULL ENTERPRISE VERSION - FIXED v2
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import re

from dotenv import load_dotenv
from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools.file import FileTools

# --------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------
load_dotenv()


class SDAConfig:
    MODEL = os.getenv("SDA_MODEL", "gemini-2.5-flash-lite")
    OUTPUT_DIR = Path("output/sda_output")
    PROMPT_DIR = Path("prompts/SDA")
    DB_FILE = "database/sda_agent.db"

    @classmethod
    def setup(cls):
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        Path("database").mkdir(parents=True, exist_ok=True)


SDAConfig.setup()


# --------------------------------------------------------------------
# LOAD PROMPTS
# --------------------------------------------------------------------
def load_prompts():
    """Load all prompt files from PROMPT_DIR"""
    prompts = {}
    prompt_files = glob.glob(str(SDAConfig.PROMPT_DIR / "*.txt"))
    
    if not prompt_files:
        print(f"⚠️  Warning: No prompt files found in {SDAConfig.PROMPT_DIR}")
        print("Creating sample prompts...")
        create_sample_prompts()
        prompt_files = glob.glob(str(SDAConfig.PROMPT_DIR / "*.txt"))
    
    for p in prompt_files:
        key = Path(p).stem  # filename without extension
        with open(p, "r", encoding="utf-8") as f:
            prompts[key] = f.read()
    
    return prompts


def create_sample_prompts():
    """Create sample prompt files if they don't exist"""
    sample_prompts = {
        "system_architecture": """You are a system architecture expert. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a comprehensive YAML document describing the system architecture including:
- Components and their responsibilities
- Communication patterns
- Technology recommendations
- Deployment considerations

Format the output as valid YAML. Do not include markdown code fences or backticks.""",

        "component_list": """You are a technical architect. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a detailed Markdown document listing all system components including:
- Component name and purpose
- Key responsibilities
- Dependencies
- Technology stack recommendations

Format the output as Markdown with clear sections.""",

        "data_model": """You are a database architect. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a comprehensive YAML document describing the data model including:
- Entity definitions
- Relationships
- Key attributes
- Indexing strategy

Format the output as valid YAML. Do not include markdown code fences or backticks.""",

        "api_boundary": """You are an API architect. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a comprehensive YAML document describing API boundaries including:
- Service endpoints
- Request/response formats
- Authentication/authorization
- Rate limiting

Format the output as valid YAML. Do not include markdown code fences or backticks.""",

        "scalability": """You are a scalability expert. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a detailed Markdown document describing the scalability plan including:
- Horizontal and vertical scaling strategies
- Load balancing approaches
- Caching strategies
- Performance optimization

Format the output as Markdown.""",

        "resiliency": """You are a reliability engineer. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a detailed Markdown document describing the resiliency plan including:
- Fault tolerance mechanisms
- Disaster recovery
- Backup strategies
- Monitoring and alerting

Format the output as Markdown.""",

        "security": """You are a security architect. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a detailed Markdown document describing the security surface including:
- Authentication and authorization
- Data encryption
- API security
- Compliance considerations

Format the output as Markdown.""",

        "handoff": """You are a technical documentation expert. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a JSON manifest for handoff to development team. The JSON should include:
- project_overview: Brief description of the project
- deliverables: List of key deliverables
- technical_decisions: Key technical decisions made
- next_steps: Recommended next steps

Output ONLY valid JSON. Do not include markdown code fences, backticks, or any other formatting. Start directly with the opening brace.""",

        "audit": """You are a technical auditor. Based on the following product specification:

{spec}

UX Blueprint (if available):
{ux}

Metadata:
{meta}

Generate a JSON audit report. The JSON should include:
- completeness_check: Assessment of specification completeness
- technical_feasibility: Evaluation of technical feasibility
- risk_assessment: Identified risks and mitigation strategies
- recommendations: Key recommendations

Output ONLY valid JSON. Do not include markdown code fences, backticks, or any other formatting. Start directly with the opening brace."""
    }
    
    for key, content in sample_prompts.items():
        filepath = SDAConfig.PROMPT_DIR / f"{key}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    print(f"✓ Created {len(sample_prompts)} sample prompts in {SDAConfig.PROMPT_DIR}")


ARTIFACT_PROMPTS = load_prompts()

# Artifact filename templates
ARTIFACT_MAP = {
    "system_architecture": "system_architecture_{ts}.yaml",
    "component_list": "component_list_{ts}.md",
    "data_model": "data_model_summary_{ts}.yaml",
    "api_boundary": "api_boundary_map_{ts}.yaml",
    "scalability": "scalability_plan_{ts}.md",
    "resiliency": "resiliency_plan_{ts}.md",
    "security": "security_surface_{ts}.md",
    "handoff": "handoff_manifest_{ts}.json",
    "audit": "sda_audit_{ts}.json"
}


# --------------------------------------------------------------------
# UTILITY FUNCTIONS
# --------------------------------------------------------------------
def clean_llm_output(content: str, expected_format: str = "text") -> str:
    """
    Clean LLM output by removing markdown code fences and extra whitespace
    
    Args:
        content: Raw LLM output
        expected_format: Expected format (json, yaml, markdown, text)
        
    Returns:
        Cleaned content
    """
    if not content:
        return ""
    
    # Remove markdown code fences
    # Pattern: ```json\n{...}\n``` or ```yaml\n...\n``` or ```\n...\n```
    content = re.sub(r'^```(?:json|yaml|markdown|md)?\s*\n', '', content.strip(), flags=re.MULTILINE)
    content = re.sub(r'\n```\s*$', '', content.strip(), flags=re.MULTILINE)
    
    # For JSON, validate and potentially fix
    if expected_format == "json":
        content = content.strip()
        # Ensure it starts with { or [
        if content and content[0] not in ['{', '[']:
            # Try to find the first { or [
            start_idx = min(
                (content.find('{') if content.find('{') != -1 else len(content)),
                (content.find('[') if content.find('[') != -1 else len(content))
            )
            if start_idx < len(content):
                content = content[start_idx:]
        
        # Try to validate JSON
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON validation warning: {e}")
            # Attempt to fix common issues
            content = content.strip()
    
    return content.strip()


# --------------------------------------------------------------------
# SDA AGENT
# --------------------------------------------------------------------
def build_llm():
    """Build the LLM agent for artifact generation"""
    return Agent(
        name="SDA-Artifact-Generator",
        model=Gemini(id=SDAConfig.MODEL),
        markdown=False,
        add_history_to_context=False,  # Deterministic per-artifact
        stream_events=False,
        debug_mode=False
    )


# --------------------------------------------------------------------
# MAIN SDA CLASS
# --------------------------------------------------------------------
class SystemDesignAgent:
    """System Design Agent for generating comprehensive system design artifacts"""

    def __init__(self):
        self.llm = build_llm()
        self.db = SqliteDb(id="sda_db", db_file=SDAConfig.DB_FILE)
        # Initialize FileTools with base directory
        self.file_tools = FileTools(base_dir=SDAConfig.OUTPUT_DIR)

    def run_artifact(self, key: str, prompt: str, context: Dict[str, str], ts: str) -> tuple[str, str]:
        """
        Execute one artifact generation prompt
        
        Args:
            key: Artifact key from ARTIFACT_MAP
            prompt: The prompt template to use
            context: Context dictionary with spec, ux, meta
            ts: Timestamp string
            
        Returns:
            Tuple of (filename, content)
        """
        filename = ARTIFACT_MAP[key].format(ts=ts)
        
        # Fill prompt template using safe string replacement
        # This avoids issues with curly braces in the prompt
        filled = prompt
        for key_name, value in context.items():
            filled = filled.replace(f"{{{key_name}}}", value)
        
        # Run LLM to generate content
        print(f"📝 Generating {key}...")
        resp: RunOutput = self.llm.run(filled)
        
        # Get raw content
        raw_content = resp.content.strip() if resp.content else "# EMPTY OUTPUT"
        
        # Determine expected format from filename
        file_ext = Path(filename).suffix.lower()
        format_map = {
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown"
        }
        expected_format = format_map.get(file_ext, "text")
        
        # Clean the content
        content = clean_llm_output(raw_content, expected_format)
        
        # Additional validation for JSON
        if expected_format == "json":
            try:
                # Validate and pretty-print JSON
                parsed = json.loads(content)
                content = json.dumps(parsed, indent=2)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON validation failed for {key}: {e}")
                print(f"📄 Raw content preview: {content[:200]}...")
                # Keep the content as-is but log the error
        
        # Save file using FileTools with CORRECT parameter order: (content, filename)
        try:
            result = self.file_tools.save_file(content, filename, overwrite=True)
            print(f"✓ Saved: {result}")
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            # Fallback: save manually
            filepath = SDAConfig.OUTPUT_DIR / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✓ Saved (manual): {filepath}")
        
        return filename, content

    def generate_system_design(
        self,
        product_spec_text: str,
        ux_blueprint_text: Optional[str] = None,
        project_id: Optional[str] = None,
        version: str = "1.0.0"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive system design artifacts
        
        Args:
            product_spec_text: Product specification as text or JSON
            ux_blueprint_text: Optional UX blueprint
            project_id: Optional project identifier
            version: Project version
            
        Returns:
            Dictionary with project metadata and artifact paths
        """
        # Use timezone-aware datetime (fixes deprecation warning)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        ts_iso = datetime.now(timezone.utc).isoformat()
        
        project_id = project_id or f"project_{ts}"
        
        # Create metadata
        meta = json.dumps({
            "project_id": project_id,
            "version": version,
            "timestamp": ts_iso,
            "model": SDAConfig.MODEL
        }, indent=2)
        
        # Build context
        ctx = {
            "spec": product_spec_text,
            "ux": ux_blueprint_text or "<none>",
            "meta": meta
        }
        
        results = {
            "project_id": project_id,
            "timestamp": ts_iso,
            "version": version,
            "model": SDAConfig.MODEL,
            "artifacts": {}
        }
        
        print(f"\n{'='*60}")
        print(f"🚀 Starting System Design Agent")
        print(f"📦 Project ID: {project_id}")
        print(f"📅 Timestamp: {ts_iso}")
        print(f"{'='*60}\n")
        
        # Generate all artifacts
        for key, filename_template in ARTIFACT_MAP.items():
            prompt = ARTIFACT_PROMPTS.get(key)
            if not prompt:
                print(f"⚠️  Warning: Missing prompt file for key: {key}, skipping...")
                continue
            
            try:
                fname, content = self.run_artifact(key, prompt, ctx, ts)
                results["artifacts"][key] = {
                    "filename": fname,
                    "path": str(SDAConfig.OUTPUT_DIR / fname),
                    "size": len(content),
                    "status": "success"
                }
            except Exception as e:
                print(f"❌ Error generating {key}: {e}")
                import traceback
                traceback.print_exc()
                results["artifacts"][key] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        # Build handoff token
        results["handoff_token"] = f"handoff_{project_id}_{ts}"
        
        # Count successes
        success_count = len([a for a in results['artifacts'].values() if a.get('status') == 'success'])
        total_count = len(results['artifacts'])
        
        print(f"\n{'='*60}")
        print(f"✅ System Design Agent Complete")
        print(f"📊 Generated {success_count}/{total_count} artifacts successfully")
        if success_count < total_count:
            failed = [k for k, v in results['artifacts'].items() if v.get('status') == 'failed']
            print(f"❌ Failed: {', '.join(failed)}")
        print(f"{'='*60}\n")
        
        return results

    def interactive_cli(self):
        """Interactive CLI mode for the agent"""
        print("\n🤖 System Design Agent - Interactive Mode")
        print("=" * 60)
        
        while True:
            print("\nOptions:")
            print("1. Generate from inline spec")
            print("2. Generate from file")
            print("3. Exit")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == "1":
                print("\nEnter product spec (JSON format, Ctrl+D when done):")
                lines = []
                try:
                    while True:
                        line = input()
                        lines.append(line)
                except EOFError:
                    pass
                
                spec_text = "\n".join(lines)
                result = self.generate_system_design(product_spec_text=spec_text)
                print("\n📊 Result Summary:")
                print(json.dumps(result, indent=2))
            
            elif choice == "2":
                spec_path = input("Enter product spec file path: ").strip()
                ux_path = input("Enter UX blueprint file path (or press Enter to skip): ").strip()
                
                try:
                    with open(spec_path, "r", encoding="utf-8") as f:
                        spec_text = f.read()
                    
                    ux_text = None
                    if ux_path:
                        with open(ux_path, "r", encoding="utf-8") as f:
                            ux_text = f.read()
                    
                    result = self.generate_system_design(
                        product_spec_text=spec_text,
                        ux_blueprint_text=ux_text
                    )
                    print("\n📊 Result Summary:")
                    print(json.dumps(result, indent=2))
                except FileNotFoundError as e:
                    print(f"❌ Error: {e}")
            
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid option")


# -------------------- USAGE EXAMPLES --------------------
def example_run_from_file(spec_path: str, ux_path: Optional[str] = None):
    """Example: Generate system design from file inputs"""
    sda = SystemDesignAgent()
    
    # Load product spec
    with open(spec_path, "r", encoding="utf-8") as f:
        spec_text = f.read()
    
    # Load UX blueprint if available
    ux_text = None
    if ux_path:
        with open(ux_path, "r", encoding="utf-8") as f:
            ux_text = f.read()
    
    # Generate system design artifacts
    result = sda.generate_system_design(
        product_spec_text=spec_text,
        ux_blueprint_text=ux_text
    )
    
    print("\n📊 RESULT SUMMARY")
    print(json.dumps(result, indent=2))


def example_simple_inline():
    """Example: Generate system design from inline spec"""
    sda = SystemDesignAgent()
    
    # Sample product spec (inline mode)
    sample_spec = json.dumps({
        "project_meta": {
            "project_id": "sample_proj_001",
            "title": "Sample Recruitment Platform",
            "description": "Manage applications, schedule interviews, and track hires."
        },
        "features": [
            {
                "id": "F-001",
                "name": "Candidate Dashboard",
                "description": "View candidate status and application history"
            },
            {
                "id": "F-002",
                "name": "Interview Scheduler",
                "description": "Schedule interviews with available time slots"
            },
            {
                "id": "F-003",
                "name": "Application Tracking",
                "description": "Track application status through the hiring pipeline"
            }
        ],
        "users": [
            {
                "role": "Recruiter",
                "goals": ["Manage candidates", "Schedule interviews", "Track hiring metrics"]
            },
            {
                "role": "Candidate",
                "goals": ["Apply to jobs", "View application status", "Schedule interviews"]
            },
            {
                "role": "Hiring Manager",
                "goals": ["Review candidates", "Provide feedback", "Make hiring decisions"]
            }
        ],
        "non_functional_requirements": {
            "performance": {
                "response_time": "500ms p95",
                "throughput": "1000 requests/second"
            },
            "availability": {
                "uptime": "99.9%",
                "recovery_time": "< 5 minutes"
            },
            "scalability": {
                "concurrent_users": "10000",
                "data_growth": "1TB/year"
            },
            "security": {
                "authentication": "OAuth 2.0 / OIDC",
                "encryption": "TLS 1.3, AES-256",
                "compliance": "GDPR, SOC 2"
            }
        }
    }, indent=2)
    
    res = sda.generate_system_design(
        product_spec_text=sample_spec,
        project_id="recruitment_platform_v1",
        version="1.0.0"
    )
    
    print("\n📊 RESULT SUMMARY")
    print(json.dumps(res, indent=2))


# -------------------- MAIN ENTRY --------------------
if __name__ == "__main__":
    print("🚀 System Design Agent - Starting...")
    print("=" * 60)
    
    # Quick inline demonstration
    example_simple_inline()
    
    # Or load from file outputs of the Product Spec Agent & UX Agent
    # example_run_from_file(
    #     "output/sia_output/task_spec_20251027_123456.json",
    #     "output/uxra_output/ux_blueprint_20251027_123500.md"
    # )
    
    # Interactive mode (optional)
    # sda = SystemDesignAgent()
    # sda.interactive_cli()