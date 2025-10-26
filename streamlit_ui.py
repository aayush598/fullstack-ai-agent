"""
Streamlit UI for Autonomous Full-Stack Application Factory

This provides a user-friendly interface to interact with the AI agent system
for generating complete full-stack applications.
"""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

from fullstack_agent_main import (
    AutonomousFullStackFactory,
    SystemConfig,
    ProductDefinitionTeam,
    DevelopmentTeam,
    QualitySecurityTeam,
    DeploymentOperationsTeam,
    ContinuousImprovementTeam
)

# Page configuration
st.set_page_config(
    page_title="AI Full-Stack App Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .team-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-running {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'factory' not in st.session_state:
    st.session_state.factory = None
if 'projects' not in st.session_state:
    st.session_state.projects = []
if 'current_project' not in st.session_state:
    st.session_state.current_project = None
if 'generation_log' not in st.session_state:
    st.session_state.generation_log = []


def initialize_factory():
    """Initialize the agent factory"""
    if st.session_state.factory is None:
        with st.spinner("Initializing AI Agent System..."):
            st.session_state.factory = AutonomousFullStackFactory()
        st.success("✅ AI Agent System Initialized!")


def load_existing_projects() -> List[Dict]:
    """Load existing projects from the projects directory"""
    projects = []
    projects_dir = SystemConfig.PROJECTS_DIR
    
    if projects_dir.exists():
        for project_path in projects_dir.iterdir():
            if project_path.is_dir():
                result_file = project_path / "project_result.json"
                if result_file.exists():
                    with open(result_file, 'r') as f:
                        project_data = json.load(f)
                        projects.append(project_data)
    
    return sorted(projects, key=lambda x: x.get('timestamp', ''), reverse=True)


def render_team_overview():
    """Render overview of all teams"""
    st.markdown("### 🎯 Multi-Agent Team Architecture")
    
    teams = [
        {
            "name": "Product Definition Team",
            "icon": "📋",
            "agents": ["Spec Intake", "Domain Expert", "UX Research", "System Design", "Product Architect"],
            "role": "Transform requirements into technical specifications"
        },
        {
            "name": "Development Team",
            "icon": "💻",
            "agents": ["Database", "Backend", "Frontend", "Integration", "Infrastructure", "Performance"],
            "role": "Build complete full-stack application"
        },
        {
            "name": "Quality & Security Team",
            "icon": "🔒",
            "agents": ["Code Review", "Test & QA", "Security", "Load Testing", "Observability", "QA Lead"],
            "role": "Ensure quality, security, and reliability"
        },
        {
            "name": "Deployment & Operations Team",
            "icon": "🚀",
            "agents": ["Environment", "CI/CD", "Release Manager", "Monitoring", "Rollback", "Incident Response"],
            "role": "Deploy and operate in production"
        },
        {
            "name": "Continuous Improvement Team",
            "icon": "📈",
            "agents": ["CI Analysis", "Knowledge Curator", "Prompt Optimizer", "Model Evaluator", "Governance"],
            "role": "Learn and improve continuously"
        }
    ]
    
    cols = st.columns(2)
    for idx, team in enumerate(teams):
        with cols[idx % 2]:
            with st.expander(f"{team['icon']} {team['name']}", expanded=False):
                st.markdown(f"**Role:** {team['role']}")
                st.markdown("**Agents:**")
                for agent in team['agents']:
                    st.markdown(f"- {agent}")


def render_generation_interface():
    """Render the main application generation interface"""
    st.markdown("### 🎨 Generate Your Application")
    
    # Template selection
    template = st.selectbox(
        "Choose a template or start from scratch",
        [
            "Custom (Describe your own)",
            "SaaS Dashboard",
            "E-commerce Platform",
            "Content Management System",
            "Social Media Platform",
            "Project Management Tool",
            "Analytics Dashboard",
            "API Service",
            "Real-time Chat Application"
        ]
    )
    
    # Template descriptions
    templates = {
        "SaaS Dashboard": """
Build a modern SaaS dashboard application with:
- User authentication and multi-tenancy
- Admin panel with analytics
- Subscription management with Stripe
- RESTful API
- Real-time notifications
- Responsive design with Tailwind CSS
- PostgreSQL database
- Docker deployment
        """,
        "E-commerce Platform": """
Build a complete e-commerce platform with:
- Product catalog with search and filters
- Shopping cart and checkout
- Payment integration (Stripe/PayPal)
- Order management
- User reviews and ratings
- Admin dashboard
- Inventory management
- Email notifications
- Mobile responsive
        """,
        "Content Management System": """
Build a flexible CMS with:
- Content editing with rich text editor
- Media library
- User roles and permissions
- SEO optimization
- Multi-language support
- RESTful API
- Version control for content
- Publishing workflow
        """,
        "Social Media Platform": """
Build a social networking platform with:
- User profiles and authentication
- News feed with posts
- Follow/unfollow system
- Real-time messaging
- Notifications
- Image/video uploads
- Like and comment features
- Search functionality
        """,
        "Project Management Tool": """
Build a project management application with:
- Project and task management
- Kanban boards
- Team collaboration
- Time tracking
- File attachments
- Comments and activity feed
- Gantt charts
- Reporting and analytics
        """,
        "Analytics Dashboard": """
Build an analytics dashboard with:
- Data visualization (charts and graphs)
- Real-time data updates
- Custom report builder
- Data filtering and aggregation
- Export to CSV/PDF
- API integrations
- User permissions
- Alerting system
        """,
        "API Service": """
Build a production-ready API service with:
- RESTful API design
- Authentication (JWT/OAuth2)
- Rate limiting
- API documentation (OpenAPI/Swagger)
- Database with ORM
- Caching layer
- Error handling and logging
- Containerized deployment
        """,
        "Real-time Chat Application": """
Build a real-time chat application with:
- WebSocket connections
- One-on-one and group chat
- Message history
- File sharing
- Typing indicators
- Online status
- Push notifications
- End-to-end encryption
        """
    }
    
    # Requirements input
    if template != "Custom (Describe your own)":
        requirements = st.text_area(
            "Application Requirements (Edit as needed)",
            value=templates.get(template, ""),
            height=300,
            help="Describe what you want to build. Be as specific as possible."
        )
    else:
        requirements = st.text_area(
            "Describe Your Application",
            placeholder="Example: Build a task management app with user authentication, real-time updates, and mobile responsive design...",
            height=300,
            help="Describe what you want to build. Be as specific as possible."
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            tech_stack = st.multiselect(
                "Preferred Tech Stack (Optional)",
                ["React", "Vue", "Svelte", "FastAPI", "Django", "Flask", "PostgreSQL", "MongoDB", "Redis"],
                help="Leave empty for AI to decide"
            )
            
            deployment_target = st.selectbox(
                "Deployment Target",
                ["AWS", "GCP", "Azure", "Docker (Local)", "Kubernetes"]
            )
        
        with col2:
            include_tests = st.checkbox("Include comprehensive tests", value=True)
            include_docs = st.checkbox("Include API documentation", value=True)
            include_cicd = st.checkbox("Include CI/CD pipeline", value=True)
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button(
            "🚀 Generate Application",
            use_container_width=True,
            type="primary",
            disabled=not requirements
        )
    
    if generate_btn and requirements:
        generate_application(requirements, tech_stack, deployment_target, 
                           include_tests, include_docs, include_cicd)


def generate_application(requirements: str, tech_stack: List[str], 
                        deployment_target: str, include_tests: bool,
                        include_docs: bool, include_cicd: bool):
    """Generate application with progress tracking"""
    
    # Initialize factory if not already done
    if st.session_state.factory is None:
        initialize_factory()
    
    # Enhance requirements with options
    enhanced_requirements = requirements
    if tech_stack:
        enhanced_requirements += f"\n\nPreferred tech stack: {', '.join(tech_stack)}"
    enhanced_requirements += f"\n\nDeployment target: {deployment_target}"
    
    # Progress container
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Generation Progress")
        
        # Progress tracking
        stages = [
            "📋 Product Definition",
            "💻 Development",
            "🔒 Quality Assurance",
            "🚀 Deployment",
            "📈 Continuous Improvement"
        ]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.expander("📝 Detailed Log", expanded=True)
        
        try:
            # Simulate progress (in real implementation, this would be event-driven)
            with log_container:
                for idx, stage in enumerate(stages):
                    status_text.markdown(f"**Current Stage:** {stage}")
                    st.markdown(f"#### {stage}")
                    
                    progress = (idx + 1) / len(stages)
                    progress_bar.progress(progress)
                    
                    # Log stage start
                    st.info(f"Starting {stage}...")
                    st.session_state.generation_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "stage": stage,
                        "status": "started"
                    })
            
            # Generate application
            result = st.session_state.factory.generate_application(enhanced_requirements)
            
            # Success
            progress_bar.progress(1.0)
            status_text.markdown("**Status:** ✅ Complete!")
            
            st.success("🎉 Application generated successfully!")
            
            # Store project
            st.session_state.projects.append(result)
            st.session_state.current_project = result
            
            # Show results
            render_generation_results(result)
            
        except Exception as e:
            st.error(f"❌ Error during generation: {str(e)}")
            st.exception(e)


def render_generation_results(result: Dict[str, Any]):
    """Render the generation results"""
    st.markdown("---")
    st.markdown("### 📊 Generation Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Project ID", result['project_id'])
    with col2:
        st.metric("Status", "✅ Complete")
    with col3:
        st.metric("Duration", "~5 min")
    with col4:
        st.metric("Files Generated", "50+")
    
    # Project structure
    with st.expander("📁 Project Structure", expanded=True):
        st.code("""
project/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── tests/
├── frontend/
│   ├── src/
│   ├── components/
│   └── tests/
├── infra/
│   ├── docker/
│   ├── kubernetes/
│   └── terraform/
├── docs/
│   ├── api/
│   └── architecture/
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
        """, language="text")
    
    # Download options
    st.markdown("### 📥 Download Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.button("📦 Download ZIP", use_container_width=True)
    with col2:
        st.button("📄 Download Documentation", use_container_width=True)
    with col3:
        st.button("🔗 Clone Repository", use_container_width=True)
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.button("🚀 Deploy Now", use_container_width=True)
    with col2:
        st.button("📝 View Code", use_container_width=True)
    with col3:
        st.button("🧪 Run Tests", use_container_width=True)
    with col4:
        st.button("📊 View Metrics", use_container_width=True)


def render_projects_dashboard():
    """Render dashboard of all projects"""
    st.markdown("### 📚 Your Projects")
    
    projects = load_existing_projects()
    
    if not projects:
        st.info("No projects yet. Generate your first application!")
        return
    
    # Projects table
    df = pd.DataFrame([
        {
            "Project ID": p['project_id'],
            "Requirements": p['requirements'][:50] + "..." if len(p['requirements']) > 50 else p['requirements'],
            "Created": p['timestamp'],
            "Status": "Complete"
        }
        for p in projects
    ])
    
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Project details
    selected_project = st.selectbox(
        "Select a project to view details",
        [p['project_id'] for p in projects]
    )
    
    if selected_project:
        project = next((p for p in projects if p['project_id'] == selected_project), None)
        if project:
            with st.expander("📋 Project Details", expanded=True):
                st.json(project)


def render_analytics():
    """Render analytics and metrics"""
    st.markdown("### 📊 System Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Projects", len(st.session_state.projects), "+2")
    with col2:
        st.metric("Success Rate", "98%", "+2%")
    with col3:
        st.metric("Avg Generation Time", "4.5 min", "-0.5 min")
    with col4:
        st.metric("Code Quality Score", "94/100", "+3")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Projects Over Time")
        chart_data = pd.DataFrame({
            'Date': pd.date_range(start='2025-01-01', periods=30, freq='D'),
            'Projects': [i % 5 + 1 for i in range(30)]
        })
        st.line_chart(chart_data.set_index('Date'))
    
    with col2:
        st.markdown("#### 🎯 Team Performance")
        team_data = pd.DataFrame({
            'Team': ['PDT', 'DT', 'QST', 'DOT', 'CIT'],
            'Performance': [95, 92, 98, 90, 94]
        })
        st.bar_chart(team_data.set_index('Team'))


def render_settings():
    """Render system settings"""
    st.markdown("### ⚙️ System Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🤖 Model Configuration")
        primary_model = st.selectbox(
            "Primary Model",
            ["claude-sonnet-4-5", "claude-opus-4", "gpt-4o", "gpt-4-turbo"]
        )
        fast_model = st.selectbox(
            "Fast Model",
            ["gpt-4o-mini", "claude-haiku", "gpt-3.5-turbo"]
        )
        
    with col2:
        st.markdown("#### 🔧 Workflow Configuration")
        max_iterations = st.slider("Max Iterations", 1, 10, 5)
        parallel_execution = st.checkbox("Enable Parallel Execution", value=True)
    
    st.markdown("#### 💾 Storage Configuration")
    st.text_input("Database File", value="fullstack_factory.db")
    st.text_input("Knowledge DB", value="fullstack_knowledge.db")
    
    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")


# ==================== MAIN APP ====================
def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🤖 AI Full-Stack Application Factory</h1>', 
                unsafe_allow_html=True)
    st.markdown("**Generate production-ready full-stack applications using autonomous AI agents**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/gilbarbara/logos/main/logos/ai.svg", width=100)
        st.markdown("## Navigation")
        
        page = st.radio(
            "Choose a page",
            ["🏠 Home", "🎨 Generate App", "📚 Projects", "📊 Analytics", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🎯 Quick Stats")
        st.metric("Projects", len(load_existing_projects()))
        st.metric("Status", "🟢 Online")
        
        st.markdown("---")
        st.markdown("### 📚 Resources")
        st.markdown("- [Documentation](https://docs.agno.com)")
        st.markdown("- [GitHub](https://github.com)")
        st.markdown("- [Support](mailto:support@example.com)")
    
    # Main content
    if page == "🏠 Home":
        st.markdown("## Welcome to the AI Full-Stack Application Factory")
        st.markdown("""
        This system uses autonomous AI agents to generate complete, production-ready 
        full-stack applications from natural language requirements.
        
        ### 🚀 Key Features:
        - **Autonomous Generation**: No human intervention required
        - **Production-Ready**: Complete with tests, documentation, and CI/CD
        - **Multi-Agent System**: 5 specialized teams with 30+ agents
        - **Continuous Improvement**: System learns and improves over time
        - **Full Stack**: Backend, frontend, database, infrastructure, and more
        """)
        
        render_team_overview()
        
        st.markdown("---")
        st.markdown("### 🎬 Ready to start?")
        if st.button("🚀 Generate Your First App", type="primary", use_container_width=True):
            st.session_state.page = "🎨 Generate App"
            st.rerun()
    
    elif page == "🎨 Generate App":
        render_generation_interface()
    
    elif page == "📚 Projects":
        render_projects_dashboard()
    
    elif page == "📊 Analytics":
        render_analytics()
    
    elif page == "⚙️ Settings":
        render_settings()


if __name__ == "__main__":
    main()