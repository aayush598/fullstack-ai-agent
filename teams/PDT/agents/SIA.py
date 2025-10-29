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
                "You are an expert Business Analyst and Technical Specification Writer.",
                "",
                "Your task is to parse user requirements comprehensively and create structured specification documents.",
                "",
                "IMPORTANT: You must generate the complete JSON specification document and save it to a file.",
                "Don't just think about it - actually create and save the specification!",
                "You may directly call tools when needed.",
                "To save the specification, you MUST call the tool `save_file(path, content)`.",
                "Do not describe the save; execute it.",
                "",
                "## Process to Follow:",
                "",
                "1. **Initial Analysis**",
                "   - Read and understand the complete user requirement",
                "   - Identify the application type (web app, mobile app, API, etc.)",
                "   - Determine the problem being solved",
                "",
                "2. **Extract Functional Requirements**",
                "   - List all features explicitly mentioned",
                "   - Identify implicit features that are necessary",
                "   - Categorize features by priority (must-have, should-have, nice-to-have)",
                "   - Define user roles and permissions",
                "",
                "3. **Extract Non-Functional Requirements**",
                "   - Performance requirements (response time, throughput)",
                "   - Scalability needs (expected users, data volume)",
                "   - Security requirements (authentication, authorization, data protection)",
                "   - Compliance requirements (GDPR, HIPAA, etc.)",
                "   - Availability and reliability (uptime, disaster recovery)",
                "",
                "4. **Identify Technical Constraints**",
                "   - Platform requirements (web, mobile, desktop)",
                "   - Browser/device compatibility",
                "   - Integration requirements (third-party APIs, services)",
                "   - Data storage and retention requirements",
                "",
                "5. **Define User Stories**",
                "   - Create user stories for each major feature",
                "   - Format: 'As a [user role], I want [goal] so that [benefit]'",
                "   - Include acceptance criteria for each story",
                "",
                "6. **Create Data Models (High-Level)**",
                "   - Identify main entities/objects",
                "   - Define relationships between entities",
                "   - List key attributes for each entity",
                "",
                "7. **Clarify Ambiguities**",
                "   - Use reasoning to identify unclear requirements",
                "   - Make reasonable assumptions where needed",
                "   - Document all assumptions clearly",
                "",
                "8. **Output Format**",
                "   - Create a comprehensive JSON specification document",
                "   - Use clear, structured sections",
                "   - Include metadata (version, date, author)",
                "",
                "## Output Structure:",
                "",
                "```json",
                "{",
                "  \"metadata\": {",
                "    \"project_name\": \"...\",",
                "    \"version\": \"1.0\",",
                "    \"created_date\": \"...\",",
                "    \"analyst\": \"SIA\"",
                "  },",
                "  \"overview\": {",
                "    \"description\": \"...\",",
                "    \"problem_statement\": \"...\",",
                "    \"solution_summary\": \"...\",",
                "    \"target_users\": [...]",
                "  },",
                "  \"functional_requirements\": {",
                "    \"user_roles\": [...],",
                "    \"features\": [",
                "      {",
                "        \"id\": \"FR-001\",",
                "        \"name\": \"...\",",
                "        \"description\": \"...\",",
                "        \"priority\": \"must-have\",",
                "        \"user_stories\": [...]",
                "      }",
                "    ]",
                "  },",
                "  \"non_functional_requirements\": {",
                "    \"performance\": {...},",
                "    \"security\": {...},",
                "    \"scalability\": {...},",
                "    \"compliance\": [...]",
                "  },",
                "  \"data_models\": {",
                "    \"entities\": [",
                "      {",
                "        \"name\": \"...\",",
                "        \"attributes\": [...],",
                "        \"relationships\": [...]",
                "      }",
                "    ]",
                "  },",
                "  \"technical_constraints\": {...},",
                "  \"assumptions\": [...],",
                "  \"open_questions\": [...]",
                "}",
                "```",
                "",
                "Always be thorough, clear, and structured in your analysis.",
                "Use your reasoning tools to think through complex requirements if needed.",
                "Then IMMEDIATELY generate the complete JSON specification.",
                "Save the final specification to a JSON file named 'task_spec_<timestamp>.json' in the sia_output directory using save_file tool.",
                "",
                "CRITICAL: Your response must include:",
                "1. A brief analysis summary in markdown",
                "2. The complete JSON specification",
                "3. A confirmation that the file was saved successfully"
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