"""
Autonomous Full-Stack Application Generator
Multi-Agent System using Agno Framework

This system can autonomously generate complete, production-grade full-stack applications
from requirements to deployment without human intervention.

Architecture: 5 Autonomous Teams in a Closed-Loop Workflow
1. Product Definition Team (PDT)
2. Development Team (DT)
3. Quality & Security Team (QST)
4. Deployment & Operations Team (DOT)
5. Continuous Improvement Team (CIT)
"""

import os
from typing import Dict, Any, List, Iterator
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

from agno.agent import Agent, RunOutput, RunOutputEvent, RunEvent
from agno.team import Team
from agno.workflow import Workflow, Step, StepInput, StepOutput, Loop, Parallel, Condition
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb
from agno.knowledge import Knowledge
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.file import FileTools
from agno.tools.reasoning import ReasoningTools
from agno.vectordb.lancedb import LanceDb

load_dotenv()

# ==================== CONFIGURATION ====================
class SystemConfig:
    """Central configuration for the autonomous agent system"""
    
    # Database Configuration
    DB_FILE = "fullstack_factory.db"
    KNOWLEDGE_DB = "fullstack_knowledge.db"
    
    # Model Configuration
    PRIMARY_MODEL = "gemini-2.5-flash-lite"
    FAST_MODEL = "gemini-2.5-flash-lite"
    REASONING_MODEL = "gemini-2.5-flash-lite"
    
    # Storage Paths
    ARTIFACTS_DIR = Path("artifacts")
    PROJECTS_DIR = Path("projects")
    LOGS_DIR = Path("logs")
    
    # Workflow Configuration
    MAX_ITERATIONS = 5
    PARALLEL_EXECUTION = True
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories"""
        for dir_path in [cls.ARTIFACTS_DIR, cls.PROJECTS_DIR, cls.LOGS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


# ==================== TEAM 1: PRODUCT DEFINITION TEAM ====================
class ProductDefinitionTeam:
    """
    Responsible for converting user requirements into detailed technical specifications
    """
    
    @staticmethod
    def create() -> Team:
        # Spec Intake Agent
        spec_intake_agent = Agent(
            name="Spec Intake Agent",
            role="Parse and structure user requirements into formal specifications",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Parse user requirements comprehensively",
                "Identify functional and non-functional requirements",
                "Create structured specification documents",
                "Clarify ambiguities using reasoning",
                "Output in JSON format with clear sections"
            ],
            markdown=True,
            add_history_to_context=True
        )
        
        # Domain Expert Agent
        domain_expert_agent = Agent(
            name="Domain Expert Agent",
            role="Enrich specifications with domain-specific best practices",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), DuckDuckGoTools()],
            instructions=[
                "Analyze the application domain",
                "Research current industry standards and best practices",
                "Identify appropriate tech stack and architecture patterns",
                "Recommend scalability and security patterns",
                "Consider regulatory and compliance requirements"
            ],
            markdown=True
        )
        
        # UX Research Agent
        ux_research_agent = Agent(
            name="UX Research Agent",
            role="Design user experience and interface structure",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), DuckDuckGoTools()],
            instructions=[
                "Create user journey maps",
                "Design information architecture",
                "Define wireframes and component hierarchy",
                "Ensure accessibility (WCAG 2.1 AA compliance)",
                "Create responsive design specifications",
                "Output detailed UX blueprint in markdown"
            ],
            markdown=True
        )
        
        # System Design Agent
        system_design_agent = Agent(
            name="System Design Agent",
            role="Create comprehensive system architecture",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Design microservices/monolithic architecture as appropriate",
                "Define database schema and relationships",
                "Plan caching and queueing strategies",
                "Design API structure (REST/GraphQL)",
                "Create deployment architecture",
                "Define monitoring and logging strategy",
                "Output system_architecture.yaml"
            ],
            markdown=True
        )
        
        # Product Architect Agent (Team Leader)
        product_architect_agent = Agent(
            name="Product Architect Agent",
            role="Finalize and validate complete product specification",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Review all specifications for completeness",
                "Ensure consistency across all documents",
                "Create final architecture document",
                "Generate API contract specifications (OpenAPI 3.0)",
                "Create comprehensive project brief",
                "Validate technical feasibility",
                "Output: architecture_doc.md, api_contract.yaml, project_brief.json"
            ],
            markdown=True,
            add_history_to_context=True
        )
        
        return Team(
            name="Product Definition Team",
            members=[
                spec_intake_agent,
                domain_expert_agent,
                ux_research_agent,
                system_design_agent,
                product_architect_agent
            ],
            role="Transform user requirements into comprehensive technical specifications",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            db=SqliteDb(id="pdt_db", db_file=SystemConfig.DB_FILE, session_table="pdt_sessions"),
            instructions=[
                "Coordinate all agents to create complete product specifications",
                "Ensure all aspects are covered: UX, architecture, APIs, security",
                "Produce production-ready specifications",
                "Delegate specific tasks to specialized agents",
                "Synthesize all outputs into cohesive documentation"
            ],
            markdown=True
        )


# ==================== TEAM 2: DEVELOPMENT TEAM ====================
class DevelopmentTeam:
    """
    Responsible for implementing the complete application based on specifications
    """
    
    @staticmethod
    def create() -> Team:
        # Database Agent
        database_agent = Agent(
            name="Database Agent",
            role="Design and implement database schema and ORM models",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools(), FileTools()],
            instructions=[
                "Create database schema from specifications",
                "Generate ORM models (SQLAlchemy/Prisma)",
                "Implement migrations",
                "Add indexes and constraints",
                "Create seed data scripts",
                "Output: schema.sql, models.py, migrations/"
            ],
            markdown=True
        )
        
        # Backend Engineer Agent
        backend_engineer_agent = Agent(
            name="Backend Engineer Agent",
            role="Build robust backend services and APIs",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools(), FileTools()],
            instructions=[
                "Implement RESTful/GraphQL APIs",
                "Create service layer with business logic",
                "Implement authentication and authorization",
                "Add input validation and error handling",
                "Create middleware for logging and monitoring",
                "Implement rate limiting and security headers",
                "Use FastAPI/Flask/Django as appropriate",
                "Output: backend/ directory with complete server code"
            ],
            markdown=True
        )
        
        # Frontend Engineer Agent
        frontend_engineer_agent = Agent(
            name="Frontend Engineer Agent",
            role="Build modern, responsive frontend applications",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Implement React/Vue/Svelte components",
                "Create responsive layouts using Tailwind CSS",
                "Implement state management (Redux/Zustand/Pinia)",
                "Add form validation and error handling",
                "Implement routing and navigation",
                "Create reusable component library",
                "Ensure accessibility compliance",
                "Output: frontend/ directory with complete UI code"
            ],
            markdown=True
        )
        
        # Integration Agent
        integration_agent = Agent(
            name="Integration Agent",
            role="Integrate frontend, backend, and external services",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools(), FileTools()],
            instructions=[
                "Connect frontend to backend APIs",
                "Implement API client with error handling",
                "Add loading states and optimistic updates",
                "Integrate third-party services (payment, email, etc.)",
                "Implement WebSocket/Server-Sent Events if needed",
                "Create unified error handling strategy",
                "Output: Integrated, working application"
            ],
            markdown=True
        )
        
        # Infrastructure Agent
        infrastructure_agent = Agent(
            name="Infrastructure Agent",
            role="Create deployment infrastructure and configurations",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Create Dockerfile for containerization",
                "Generate docker-compose.yml for local development",
                "Create Kubernetes manifests if needed",
                "Setup CI/CD pipelines (GitHub Actions/GitLab CI)",
                "Create environment configuration templates",
                "Generate infrastructure-as-code (Terraform/Pulumi)",
                "Output: infra/ directory with all configs"
            ],
            markdown=True
        )
        
        # Performance Optimization Agent
        performance_optimization_agent = Agent(
            name="Performance Optimization Agent",
            role="Optimize application performance and resource usage",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools()],
            instructions=[
                "Profile application performance",
                "Optimize database queries",
                "Implement caching strategies (Redis/Memcached)",
                "Optimize bundle size and loading times",
                "Add lazy loading and code splitting",
                "Implement CDN configuration",
                "Create performance benchmark reports",
                "Output: performance_report.md with metrics"
            ],
            markdown=True
        )
        
        # Development Lead Agent (Team Leader)
        dev_lead_agent = Agent(
            name="Development Lead Agent",
            role="Orchestrate development team and ensure code quality",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Coordinate all development agents",
                "Ensure code follows best practices and standards",
                "Review architecture implementation",
                "Verify all specifications are met",
                "Create comprehensive README.md",
                "Generate API documentation",
                "Package complete application repository",
                "Output: Complete, documented codebase ready for testing"
            ],
            markdown=True,
            add_history_to_context=True
        )
        
        return Team(
            name="Development Team",
            members=[
                database_agent,
                backend_engineer_agent,
                frontend_engineer_agent,
                integration_agent,
                infrastructure_agent,
                performance_optimization_agent,
                dev_lead_agent
            ],
            role="Build complete, production-ready full-stack application",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            db=SqliteDb(id="dt_db", db_file=SystemConfig.DB_FILE, session_table="dt_sessions"),
            instructions=[
                "Implement complete application from specifications",
                "Ensure high code quality and maintainability",
                "Follow industry best practices and design patterns",
                "Create modular, testable code",
                "Document all code thoroughly"
            ],
            markdown=True
        )


# ==================== TEAM 3: QUALITY & SECURITY TEAM ====================
class QualitySecurityTeam:
    """
    Responsible for comprehensive testing and security validation
    """
    
    @staticmethod
    def create() -> Team:
        # Code Review Agent
        code_review_agent = Agent(
            name="Code Review Agent",
            role="Perform comprehensive code review and quality analysis",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools(), FileTools()],
            instructions=[
                "Perform static code analysis",
                "Check code style and formatting (Ruff/ESLint)",
                "Identify code smells and anti-patterns",
                "Check for code duplication",
                "Verify proper error handling",
                "Ensure logging is appropriate",
                "Output: code_review_report.md"
            ],
            markdown=True
        )
        
        # Test & QA Agent
        test_qa_agent = Agent(
            name="Test & QA Agent",
            role="Create and execute comprehensive test suites",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools(), FileTools()],
            instructions=[
                "Generate unit tests (Pytest/Jest)",
                "Create integration tests",
                "Implement end-to-end tests (Playwright/Cypress)",
                "Create API tests (Postman/REST-assured)",
                "Achieve >80% code coverage",
                "Test edge cases and error scenarios",
                "Output: tests/ directory and test_report.json"
            ],
            markdown=True
        )
        
        # Security Agent
        security_agent = Agent(
            name="Security Agent",
            role="Perform security audits and vulnerability scanning",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Perform SAST (Static Application Security Testing)",
                "Check for OWASP Top 10 vulnerabilities",
                "Scan dependencies for known vulnerabilities",
                "Verify authentication and authorization implementation",
                "Check for secure credential management",
                "Verify HTTPS and security headers",
                "Test for SQL injection, XSS, CSRF",
                "Output: security_report.json with severity levels"
            ],
            markdown=True
        )
        
        # Load Testing Agent
        load_testing_agent = Agent(
            name="Load Testing Agent",
            role="Perform load and stress testing",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), PythonTools()],
            instructions=[
                "Create load testing scripts (Locust/K6)",
                "Test API endpoints under load",
                "Measure response times and throughput",
                "Identify performance bottlenecks",
                "Test database connection pooling",
                "Verify auto-scaling behavior",
                "Output: load_test_results.json"
            ],
            markdown=True
        )
        
        # Observability Agent
        observability_agent = Agent(
            name="Observability Agent",
            role="Implement monitoring and observability",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Add structured logging (JSON format)",
                "Implement distributed tracing (OpenTelemetry)",
                "Add application metrics (Prometheus)",
                "Create health check endpoints",
                "Implement error tracking (Sentry)",
                "Create monitoring dashboards (Grafana)",
                "Output: observability_config.yaml"
            ],
            markdown=True
        )
        
        # QA Lead Agent (Team Leader)
        qa_lead_agent = Agent(
            name="QA Lead Agent",
            role="Oversee quality assurance and make go/no-go decisions",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Review all test and security reports",
                "Aggregate quality metrics",
                "Make go/no-go decision for deployment",
                "Create comprehensive QA summary",
                "If tests fail, provide detailed feedback for Development Team",
                "If tests pass, approve for deployment",
                "Output: qa_decision.json with PASS/FAIL status"
            ],
            markdown=True,
            add_history_to_context=True
        )
        
        return Team(
            name="Quality & Security Team",
            members=[
                code_review_agent,
                test_qa_agent,
                security_agent,
                load_testing_agent,
                observability_agent,
                qa_lead_agent
            ],
            role="Ensure application quality, security, and reliability",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            db=SqliteDb(id="qst_db", db_file=SystemConfig.DB_FILE, session_table="qst_sessions"),
            instructions=[
                "Perform comprehensive testing and security audits",
                "Ensure application meets quality standards",
                "Identify and report all issues",
                "Make informed go/no-go decisions"
            ],
            markdown=True
        )


# ==================== TEAM 4: DEPLOYMENT & OPERATIONS TEAM ====================
class DeploymentOperationsTeam:
    """
    Responsible for deploying and operating the application in production
    """
    
    @staticmethod
    def create() -> Team:
        # Environment Provisioning Agent
        env_provisioning_agent = Agent(
            name="Environment Provisioning Agent",
            role="Provision and configure cloud infrastructure",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Provision cloud resources (AWS/GCP/Azure)",
                "Configure networking and security groups",
                "Setup databases and storage",
                "Configure load balancers",
                "Setup DNS and SSL certificates",
                "Output: environment_state.json"
            ],
            markdown=True
        )
        
        # CI/CD Pipeline Agent
        cicd_agent = Agent(
            name="CI/CD Pipeline Agent",
            role="Create and manage deployment pipelines",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Create GitHub Actions/GitLab CI pipelines",
                "Implement automated testing in pipeline",
                "Setup Docker image builds and registry pushes",
                "Implement blue-green or canary deployments",
                "Add automatic rollback on failure",
                "Output: .github/workflows/ or .gitlab-ci.yml"
            ],
            markdown=True
        )
        
        # Release Manager Agent
        release_manager_agent = Agent(
            name="Release Manager Agent",
            role="Manage application releases and deployments",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Execute deployment to staging environment",
                "Perform smoke tests in staging",
                "Execute production deployment",
                "Verify deployment success",
                "Create release notes",
                "Output: deployment_manifest.yaml"
            ],
            markdown=True
        )
        
        # Monitoring Agent
        monitoring_agent = Agent(
            name="Monitoring Agent",
            role="Monitor application health and performance",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Monitor application metrics",
                "Track error rates and latency",
                "Monitor resource utilization",
                "Setup alerting rules",
                "Create monitoring dashboards",
                "Output: monitoring_config.yaml and telemetry_logs.json"
            ],
            markdown=True
        )
        
        # Rollback Agent
        rollback_agent = Agent(
            name="Rollback Agent",
            role="Handle deployment rollbacks and recovery",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Detect deployment failures",
                "Execute automatic rollback procedures",
                "Restore database backups if needed",
                "Verify rollback success",
                "Document rollback reasons",
                "Output: rollback_report.json"
            ],
            markdown=True
        )
        
        # Incident Response Agent
        incident_response_agent = Agent(
            name="Incident Response Agent",
            role="Handle production incidents and issues",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Detect and classify incidents",
                "Perform root cause analysis",
                "Coordinate incident response",
                "Create incident reports",
                "Implement immediate fixes if needed",
                "Output: incident_reports.json"
            ],
            markdown=True
        )
        
        # Operations Lead Agent (Team Leader)
        ops_lead_agent = Agent(
            name="Operations Lead Agent",
            role="Oversee deployment operations and system reliability",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Coordinate all deployment activities",
                "Ensure zero-downtime deployments",
                "Monitor overall system health",
                "Make critical operational decisions",
                "Escalate issues to Continuous Improvement Team",
                "Output: deployment_summary.json"
            ],
            markdown=True,
            add_history_to_context=True
        )
        
        return Team(
            name="Deployment & Operations Team",
            members=[
                env_provisioning_agent,
                cicd_agent,
                release_manager_agent,
                monitoring_agent,
                rollback_agent,
                incident_response_agent,
                ops_lead_agent
            ],
            role="Deploy and operate application in production",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            db=SqliteDb(id="dot_db", db_file=SystemConfig.DB_FILE, session_table="dot_sessions"),
            instructions=[
                "Deploy application safely to production",
                "Ensure system reliability and availability",
                "Monitor and respond to incidents",
                "Maintain operational excellence"
            ],
            markdown=True
        )


# ==================== TEAM 5: CONTINUOUS IMPROVEMENT TEAM ====================
class ContinuousImprovementTeam:
    """
    Responsible for learning from operations and continuously improving the system
    """
    
    @staticmethod
    def create() -> Team:
        # Continuous Improvement Agent
        ci_agent = Agent(
            name="Continuous Improvement Agent",
            role="Analyze system performance and identify improvements",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Analyze deployment success/failure rates",
                "Identify recurring issues and patterns",
                "Measure development velocity",
                "Track quality metrics over time",
                "Recommend process improvements",
                "Output: improvement_recommendations.json"
            ],
            markdown=True
        )
        
        # Knowledge Curator Agent
        knowledge_curator_agent = Agent(
            name="Knowledge Curator Agent",
            role="Curate and update organizational knowledge base",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            knowledge=Knowledge(
                vector_db=LanceDb(
                    table_name="cit_knowledge",
                    uri="tmp/lancedb"
                ),
            ),
            instructions=[
                "Extract learnings from project execution",
                "Update best practices documentation",
                "Index successful patterns and solutions",
                "Create reusable templates and snippets",
                "Maintain tech stack knowledge",
                "Output: Updated knowledge base"
            ],
            markdown=True
        )
        
        # Prompt Optimization Agent
        prompt_optimization_agent = Agent(
            name="Prompt Optimization Agent",
            role="Optimize agent instructions and prompts",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Analyze agent performance logs",
                "Identify suboptimal agent outputs",
                "Refine agent instructions and prompts",
                "Test improved prompts",
                "Version control prompt changes",
                "Output: updated_prompts.yaml"
            ],
            markdown=True
        )
        
        # Model Evaluation Agent
        model_evaluation_agent = Agent(
            name="Model Evaluation Agent",
            role="Evaluate and optimize model selection",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools()],
            instructions=[
                "Track model performance metrics",
                "Compare different models for specific tasks",
                "Optimize cost vs. performance trade-offs",
                "Recommend model upgrades or changes",
                "Output: model_evaluation_report.json"
            ],
            markdown=True
        )
        
        # Governance Agent
        governance_agent = Agent(
            name="Governance Agent",
            role="Ensure compliance and ethical AI practices",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Verify ethical AI practices",
                "Ensure data privacy compliance",
                "Check licensing compliance",
                "Audit AI decision-making processes",
                "Monitor for bias in generated code",
                "Output: governance_report.json"
            ],
            markdown=True
        )
        
        # Report Generator Agent
        report_generator_agent = Agent(
            name="Report Generator Agent",
            role="Generate comprehensive improvement reports",
            model=Gemini(id=SystemConfig.PRIMARY_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Aggregate all improvement insights",
                "Create executive summaries",
                "Generate trend analysis",
                "Produce actionable recommendations",
                "Output: comprehensive_report.md"
            ],
            markdown=True
        )
        
        # Improvement Lead Agent (Team Leader)
        improvement_lead_agent = Agent(
            name="Improvement Lead Agent",
            role="Lead continuous improvement initiatives",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            tools=[ReasoningTools(), FileTools()],
            instructions=[
                "Synthesize all improvement recommendations",
                "Prioritize improvements by impact",
                "Decide which improvements to implement",
                "Provide feedback to Product Definition and Development Teams",
                "Determine if workflow should continue or restart",
                "Output: feedback.json with improvement_needed flag"
            ],
            markdown=True,
            add_history_to_context=True
        )
        
        return Team(
            name="Continuous Improvement Team",
            members=[
                ci_agent,
                knowledge_curator_agent,
                prompt_optimization_agent,
                model_evaluation_agent,
                governance_agent,
                report_generator_agent,
                improvement_lead_agent
            ],
            role="Drive continuous improvement and learning",
            model=Gemini(id=SystemConfig.REASONING_MODEL),
            db=SqliteDb(id="pdt_db", db_file=SystemConfig.DB_FILE, session_table="cit_sessions"),
            instructions=[
                "Learn from every project execution",
                "Continuously improve system capabilities",
                "Provide actionable feedback to all teams",
                "Maintain organizational knowledge"
            ],
            markdown=True
        )

def qa_passed(step_input: StepInput) -> bool:
    """Evaluator for QA condition"""
    output = step_input.previous_step_content
    if isinstance(output, str):
        return "PASS" in output.upper()
    elif isinstance(output, dict):
        return output.get("status", "").upper() == "PASS"
    return False

# ==================== MAIN WORKFLOW ORCHESTRATOR ====================
class AutonomousFullStackFactory:
    """
    Main orchestrator for the autonomous full-stack application factory
    """
    
    def __init__(self):
        SystemConfig.setup_directories()
        
        # Initialize all teams
        self.pdt = ProductDefinitionTeam.create()
        self.dt = DevelopmentTeam.create()
        self.qst = QualitySecurityTeam.create()
        self.dot = DeploymentOperationsTeam.create()
        self.cit = ContinuousImprovementTeam.create()
        
        # Create the main workflow
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> Workflow:
        """Create the main autonomous workflow"""
        
        workflow = Workflow(
            name="Autonomous Full-Stack Application Factory",
            steps=[
                Step(
                    name="Product Definition",
                    team=self.pdt,
                    description="Transform requirements into technical specifications"
                ),
                Step(
                    name="Development",
                    team=self.dt,
                    description="Build complete full-stack application"
                ),
                Step(
                    name="Quality Assurance",
                    team=self.qst,
                    description="Test and validate application"
                ),
                # Conditional deployment based on QA results
                Condition(
                    name="QA_Pass_Condition",
                    description="Check if QA passed before deployment",
                    evaluator=qa_passed,
                    steps=[
                        Step(
                            name="Deployment",
                            team=self.dot,
                            description="Deploy to production"
                        )
                    ]
                ),
                Step(
                    name="Continuous Improvement",
                    team=self.cit,
                    description="Analyze and improve system"
                )
            ]
        )
        
        return workflow
    
    def _check_qa_pass(self, qa_output: Any) -> bool:
        """Check if QA tests passed"""
        try:
            if isinstance(qa_output, str):
                return "PASS" in qa_output.upper()
            elif isinstance(qa_output, dict):
                return qa_output.get("status") == "PASS"
            return False
        except:
            return False
    
    def generate_application(self, user_requirements: str) -> Dict[str, Any]:
        """
        Main entry point to generate a complete full-stack application
        
        Args:
            user_requirements: Natural language description of the application
            
        Returns:
            Dictionary containing project information and status
        """
        print(f"🚀 Starting Autonomous Full-Stack Application Factory")
        print(f"📝 Requirements: {user_requirements}")
        print("=" * 80)
        
        # Create project metadata
        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        project_dir = SystemConfig.PROJECTS_DIR / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Execute workflow
        result = self.workflow.run(user_requirements)
        
        # Save results
        result_file = project_dir / "project_result.json"
        with open(result_file, 'w') as f:
            json.dump({
                "project_id": project_id,
                "requirements": user_requirements,
                "timestamp": datetime.now().isoformat(),
                "result": str(result.content) if hasattr(result, 'content') else str(result)
            }, f, indent=2)
        
        print("=" * 80)
        print(f"✅ Application generation complete!")
        print(f"📁 Project saved to: {project_dir}")
        
        return {
            "project_id": project_id,
            "project_dir": str(project_dir),
            "status": "completed",
            "result": result
        }


# ==================== ENTRY POINT ====================
if __name__ == "__main__":
    # Example usage
    factory = AutonomousFullStackFactory()
    
    # Test with a sample requirement
    requirements = """
    Build a SaaS task management application with the following features:
    - User authentication and authorization
    - Create, read, update, delete tasks
    - Task categories and tags
    - Due dates and reminders
    - Team collaboration features
    - Real-time updates
    - Mobile responsive design
    - Export data to CSV/PDF
    """
    
    result = factory.generate_application(requirements)
    print(f"\n🎉 Project ID: {result['project_id']}")
    print(f"📂 Location: {result['project_dir']}")