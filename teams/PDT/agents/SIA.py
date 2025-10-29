"""
Specification Intake Agent (SIA)
Standalone implementation using Agno Framework

This agent parses user requirements and structures them into formal specifications
with real-time progress tracking and comprehensive debugging.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from agno.agent import Agent, RunOutput, RunOutputEvent, RunEvent
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.tools.reasoning import ReasoningTools
from agno.tools.file import FileTools
from agno.utils.pprint import pprint_run_response

load_dotenv()

# ==================== CONFIGURATION ====================
class SIAConfig:
    """Configuration for Specification Intake Agent"""
    
    # Model Configuration
    MODEL = "gemini-2.5-flash-lite"
    
    # Storage Paths
    OUTPUT_DIR = Path("sia_output")
    DB_FILE = "sia_agent.db"
    
    # Debug Settings
    DEBUG_MODE = True
    DEBUG_LEVEL = 2  # Higher level = more detailed logs
    
    @classmethod
    def setup(cls):
        """Setup directories and environment"""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Output directory created: {cls.OUTPUT_DIR}")


# ==================== SPECIFICATION INTAKE AGENT ====================
class SpecificationIntakeAgent:
    """
    Autonomous agent that parses and structures user requirements
    into comprehensive technical specifications
    """
    
    def __init__(self):
        SIAConfig.setup()
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create and configure the Specification Intake Agent"""
        
        agent = Agent(
            name="Specification Intake Agent (SIA)",
            role="Parse and structure user requirements into formal specifications",
            model=Gemini(id=SIAConfig.MODEL),
            tool_choice="auto",
            
            # Tools
            tools=[
                ReasoningTools(),  # For analyzing and reasoning about requirements
                FileTools()        # For writing specification files
            ],
            
            # Database for session management
            db=SqliteDb(
                id="sia_db",
                db_file=SIAConfig.DB_FILE,
                session_table="sia_sessions"
            ),
            
            # Instructions - The core programming of the agent
            instructions=[
    "You are the **Specification Intake Agent (SIA)** — a senior-level Business Analyst and Technical Specification Author.",
    "Your mission is to transform raw user or stakeholder requirements into a **complete, professionally structured software specification document**.",
    "",
    "You DO NOT design UI/UX, choose tech stacks, define architectures, or generate diagrams — those are handled by other agents.",
    "You ONLY focus on high-quality business and functional specifications with clear boundaries, context, and actionable requirements.",
    "",
    "### 🎯 Your Core Responsibilities",
    "1. Interpret user inputs and derive a clear, formalized problem statement.",
    "2. Identify application scope, use cases, roles, and goals.",
    "3. Translate vague or incomplete requirements into structured, precise, and unambiguous specifications.",
    "4. Capture all **functional and non-functional requirements** relevant to business operations and system behavior.",
    "5. Highlight ambiguities, missing information, or dependencies.",
    "6. Present outputs in a **JSON document format** for machine-readable consistency.",
    "",
    "### ⚙️ Output Rules",
    "- Always generate and SAVE the final specification file to `sia_output/task_spec_<timestamp>.json` using `save_file(path, content)`.",
    "- Do not describe the save; actually execute the save_file tool.",
    "- Include all core sections of a software specification, but avoid implementation or design details.",
    "",
    "### 🧩 Specification Composition",
    "Your structured output should contain the following key sections:",
    "",
    "```json",
    "{",
    "  \"metadata\": {",
    "    \"project_name\": \"...\",",
    "    \"version\": \"1.0\",",
    "    \"created_date\": \"...\",",
    "    \"analyst\": \"SIA\"",
    "  },",
    "  \"business_context\": {",
    "    \"overview\": \"High-level description of the system and purpose.\",",
    "    \"problem_statement\": \"Summarized problem the system solves.\",",
    "    \"goals_and_objectives\": [\"Business goals, value, or KPIs\"],",
    "    \"target_users\": [\"Primary user types\"],",
    "    \"assumptions\": [\"Business or technical assumptions\"],",
    "    \"out_of_scope\": [\"Items explicitly excluded\"]",
    "  },",
    "  \"functional_requirements\": {",
    "    \"user_roles\": [\"List of roles and their permissions or capabilities\"],",
    "    \"core_features\": [",
    "      {",
    "        \"id\": \"FR-001\",",
    "        \"name\": \"Feature name\",",
    "        \"description\": \"Detailed description of functionality\",",
    "        \"priority\": \"must-have|should-have|nice-to-have\",",
    "        \"user_stories\": [\"As a [role], I want [goal] so that [benefit]\"],",
    "        \"dependencies\": [\"Other features or external systems\"]",
    "      }",
    "    ]",
    "  },",
    "  \"non_functional_requirements\": {",
    "    \"performance\": {\"response_time\": \"...\", \"throughput\": \"...\"},",
    "    \"scalability\": {\"expected_users\": \"...\", \"growth_targets\": \"...\"},",
    "    \"security\": {\"authentication\": \"...\", \"authorization\": \"...\", \"data_protection\": \"...\"},",
    "    \"availability\": {\"uptime\": \"...\", \"failover\": \"...\"},",
    "    \"compliance\": [\"GDPR\", \"HIPAA\", \"ISO27001\", \"...\"],",
    "    \"usability\": {\"accessibility\": \"...\", \"localization\": \"...\"},",
    "    \"maintenance\": {\"support_model\": \"...\", \"update_frequency\": \"...\"}",
    "  },",
    "  \"data_requirements\": {",
    "    \"entities\": [",
    "      {",
    "        \"name\": \"Entity name\",",
    "        \"description\": \"Purpose of entity\",",
    "        \"key_fields\": [\"id\", \"name\", \"...\"],",
    "        \"sensitive_data\": true|false",
    "      }",
    "    ],",
    "    \"data_retention_policy\": \"Describe how long data is retained and where\"",
    "  },",
    "  \"integration_points\": {",
    "    \"external_systems\": [\"Payment gateway\", \"Email API\", \"Analytics\"],",
    "    \"interfaces\": [\"Describe expected API inputs/outputs conceptually\"]",
    "  },",
    "  \"risk_and_constraints\": {",
    "    \"risks\": [\"Potential delivery or scope risks\"],",
    "    \"constraints\": [\"Business, legal, or operational constraints\"]",
    "  },",
    "  \"open_questions\": [\"List of unknowns or unclear requirements\"],",
    "  \"next_steps\": [\"Suggested clarifications or information required\"]",
    "}",
    "```",
    "",
    "### 🧠 Process Flow",
    "1. **Requirement Understanding** – Analyze the input text, extract goals, features, roles, and context.",
    "2. **Decomposition** – Break requirements into functional areas and measurable conditions.",
    "3. **Validation** – Ensure every feature is logically connected to a business goal or user story.",
    "4. **Completeness Check** – Identify missing requirements or edge cases.",
    "5. **Specification Assembly** – Compile results in the JSON structure with clear formatting and identifiers.",
    "6. **Persistence** – Save to file using FileTools, confirm file save in output.",
    "",
    "### 🧾 Output Expectation",
    "- Start with a short **summary of analysis (Markdown)** — summarizing business purpose and main requirement themes.",
    "- Then include the **complete JSON specification**.",
    "- End with a **confirmation that the file was successfully saved**.",
    "",
    "### 🚫 Exclusions (handled by other agents)",
    "- Do NOT include: architecture design, technology stacks, database schema design, UI/UX wireframes, or embeddings.",
    "- Do NOT generate diagrams, pseudocode, or system-level components.",
    "",
    "Be clear, formal, business-oriented, and structured — the output must read like a real enterprise specification document ready for further refinement by technical teams."
],

            # Configuration
            markdown=True,
            add_history_to_context=True,
            num_history_runs=3,
            
            # Debug mode for detailed logging
            debug_mode=SIAConfig.DEBUG_MODE,
            debug_level=SIAConfig.DEBUG_LEVEL,
            
            # Show tool calls in the output
            stream_events=True
        )
        
        return agent
    
    def process_requirements(
        self, 
        user_requirements: str,
        stream: bool = True,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process user requirements and generate structured specifications
        
        Args:
            user_requirements: Natural language description of requirements
            stream: Whether to stream the output in real-time
            session_id: Optional session ID for conversation continuity
            
        Returns:
            Dictionary with processing results and file paths
        """
        
        print("\n" + "=" * 80)
        print("🚀 SPECIFICATION INTAKE AGENT - STARTING ANALYSIS")
        print("=" * 80)
        print(f"📝 Input Requirements:\n{user_requirements}\n")
        print("=" * 80)
        
        # Create session ID if not provided
        if not session_id:
            session_id = f"sia_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Prepare the prompt
        prompt = f"""
Analyze the following user requirements and create a comprehensive technical specification document.

USER REQUIREMENTS:
{user_requirements}

TASK:
1. Analyze these requirements carefully
2. Create a complete JSON specification following the structure in your instructions
3. Save the specification to sia_output/task_spec_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json using the save_file tool

Provide a brief summary of your analysis, then the complete JSON specification, and confirm the file was saved.
"""
        
        # Track results
        results = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "requirements": user_requirements,
            "specification_file": None,
            "status": "in_progress"
        }
        
        try:
            if stream:
                # Stream the response with real-time progress
                print("\n📊 STREAMING AGENT RESPONSE:")
                print("-" * 80 + "\n")
                
                stream_output = self.agent.run(
                    prompt,
                    stream=True,
                    stream_events=True,  # Stream all events for detailed tracking
                    session_id=session_id
                )
                
                # Process and display streaming events
                full_content = ""
                for event in stream_output:
                    self._handle_stream_event(event)
                    
                    # Collect content
                    if event.event == RunEvent.run_content:
                        full_content += event.content or ""
                
                results["content"] = full_content
                results["status"] = "completed"
                
            else:
                # Non-streaming mode
                print("\n📊 AGENT PROCESSING (Non-streaming):")
                print("-" * 80 + "\n")
                
                response: RunOutput = self.agent.run(
                    prompt,
                    session_id=session_id
                )
                
                # Display response
                print(response.content)
                
                results["content"] = response.content
                results["run_id"] = response.run_id
                
                # Access metrics attributes directly (not with .get())
                results["metrics"] = {
                    "input_tokens": response.metrics.input_tokens or 0,
                    "output_tokens": response.metrics.output_tokens or 0,
                    "total_tokens": response.metrics.total_tokens or 0,
                    "time_seconds": response.metrics.duration or 0,
                    "time_to_first_token": response.metrics.time_to_first_token or 0
                }
                results["status"] = "completed"
            
            # Check for generated files
            spec_files = list(SIAConfig.OUTPUT_DIR.glob("*.json"))
            if spec_files:
                results["specification_file"] = str(spec_files[-1])  # Most recent file
                print(f"\n✅ Specification saved to: {results['specification_file']}")
            
            print("\n" + "=" * 80)
            print("✅ ANALYSIS COMPLETE")
            print("=" * 80)
            
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            print(f"\n❌ ERROR: {e}")
            print("=" * 80)
        
        return results
    
    def _handle_stream_event(self, event: RunOutputEvent):
        """Handle and display streaming events with detailed progress tracking"""
        
        if event.event == RunEvent.run_started:
            print(f"🎬 Run Started - ID: {event.run_id}")
            print(f"   Session: {event.session_id}")
            print()
            
        elif event.event == RunEvent.run_content:
            # Print content as it streams
            print(event.content or "", end="", flush=True)
            
        elif event.event == RunEvent.tool_call_started:
            print(f"\n\n🔧 TOOL CALL STARTED")
            print(f"   Tool: {event.tool_name}")
            print(f"   Function: {event.function_name if hasattr(event, 'function_name') else 'N/A'}")
            if hasattr(event, 'tool_args'):
                print(f"   Arguments: {json.dumps(event.tool_args, indent=2)}")
            print()
            
        elif event.event == RunEvent.tool_call_completed:
            print(f"\n✅ TOOL CALL COMPLETED")
            print(f"   Tool: {event.tool_name}")
            if hasattr(event, 'tool_result'):
                result_preview = str(event.tool_result)[:200]
                print(f"   Result Preview: {result_preview}...")
            print()
            
        elif event.event == RunEvent.reasoning_started:
            print(f"\n🧠 REASONING STARTED")
            print()
            
        elif event.event == RunEvent.reasoning_step:
            print(f"💭 Reasoning: {event.content}")
            print()
            
        elif event.event == RunEvent.reasoning_completed:
            print(f"✅ REASONING COMPLETED")
            print()
            
        elif event.event == RunEvent.run_completed:
            print(f"\n\n🏁 RUN COMPLETED")
            if hasattr(event, 'metrics'):
                print(f"   Metrics: {event.metrics}")
            print()
    
    def interactive_mode(self):
        """Run the agent in interactive CLI mode for testing"""
        print("\n" + "=" * 80)
        print("🎯 SPECIFICATION INTAKE AGENT - INTERACTIVE MODE")
        print("=" * 80)
        print("Type your requirements and press Enter.")
        print("Type 'exit' or 'quit' to stop.")
        print("=" * 80 + "\n")
        
        self.agent.cli_app(stream=True)


# ==================== USAGE EXAMPLES ====================
def example_simple_task_manager():
    """Example 1: Simple Task Management App"""
    
    sia = SpecificationIntakeAgent()
    
    requirements = """
    Build a task management application with the following features:
    - User registration and login
    - Create, view, edit, and delete tasks
    - Each task should have: title, description, due date, priority, status
    - Tasks can be organized into projects
    - Users should be able to filter tasks by status and priority
    - Send email notifications for upcoming due dates
    - Mobile responsive design
    """
    
    results = sia.process_requirements(requirements, stream=False)
    
    print("\n📋 RESULTS SUMMARY:")
    print(json.dumps(results, indent=2))


def example_ecommerce_platform():
    """Example 2: E-commerce Platform"""
    
    sia = SpecificationIntakeAgent()
    
    requirements = """
    Create an e-commerce platform with these capabilities:
    
    Customer Features:
    - Browse products by category
    - Search products with filters
    - Product details with images and reviews
    - Shopping cart management
    - Checkout with multiple payment methods
    - Order tracking
    - User profile management
    
    Admin Features:
    - Product catalog management
    - Order management
    - Customer management
    - Analytics dashboard
    - Inventory tracking
    
    Technical Requirements:
    - Must handle 10,000 concurrent users
    - 99.9% uptime
    - PCI DSS compliant for payments
    - GDPR compliant for user data
    """
    
    results = sia.process_requirements(requirements, stream=True)
    
    print("\n📋 RESULTS SUMMARY:")
    print(json.dumps(results, indent=2))


def example_interactive():
    """Example 3: Interactive Mode"""
    
    sia = SpecificationIntakeAgent()
    sia.interactive_mode()


# ==================== MAIN ENTRY POINT ====================
if __name__ == "__main__":
    # Choose which example to run:
    
    # Example 1: Simple task manager
    example_simple_task_manager()
    
    # Example 2: E-commerce platform
    # example_ecommerce_platform()
    
    # Example 3: Interactive mode
    # example_interactive()