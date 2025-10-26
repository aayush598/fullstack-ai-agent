"""
AgentOS FastAPI Server
Production-ready server for managing and monitoring the AI agent system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import json
from pathlib import Path

from agno.os import AgentOS
from fullstack_agent_main import (
    AutonomousFullStackFactory,
    SystemConfig,
    ProductDefinitionTeam,
    DevelopmentTeam,
    QualitySecurityTeam,
    DeploymentOperationsTeam,
    ContinuousImprovementTeam
)

# ==================== MODELS ====================
class GenerationRequest(BaseModel):
    """Request model for application generation"""
    requirements: str = Field(..., description="Natural language requirements")
    tech_stack: Optional[List[str]] = Field(default=None, description="Preferred tech stack")
    deployment_target: Optional[str] = Field(default="AWS", description="Deployment target")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options")


class GenerationResponse(BaseModel):
    """Response model for application generation"""
    project_id: str
    status: str
    message: str
    project_dir: Optional[str] = None


class ProjectStatus(BaseModel):
    """Model for project status"""
    project_id: str
    status: str
    stage: str
    progress: float
    started_at: str
    updated_at: str


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime: float
    active_projects: int


# ==================== INITIALIZE APP ====================
app = FastAPI(
    title="Autonomous Full-Stack Application Factory API",
    description="AI-powered system for generating complete full-stack applications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
factory: Optional[AutonomousFullStackFactory] = None
active_projects: Dict[str, Dict[str, Any]] = {}
start_time = datetime.now()


# ==================== STARTUP & SHUTDOWN ====================
@app.on_event("startup")
async def startup_event():
    """Initialize the agent factory on startup"""
    global factory
    try:
        SystemConfig.setup_directories()
        factory = AutonomousFullStackFactory()
        print("✅ Agent Factory initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Agent Factory: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Agent Factory...")


# ==================== ENDPOINTS ====================
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Autonomous Full-Stack Application Factory API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - start_time).total_seconds()
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        uptime=uptime,
        active_projects=len(active_projects)
    )


@app.post("/generate", response_model=GenerationResponse)
async def generate_application(
    request: GenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a complete full-stack application from requirements
    """
    if factory is None:
        raise HTTPException(status_code=500, detail="Agent factory not initialized")
    
    try:
        # Create project ID
        project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize project status
        active_projects[project_id] = {
            "status": "initializing",
            "stage": "Product Definition",
            "progress": 0.0,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Start generation in background
        background_tasks.add_task(
            run_generation,
            project_id,
            request.requirements,
            request.tech_stack,
            request.deployment_target,
            request.options
        )
        
        return GenerationResponse(
            project_id=project_id,
            status="started",
            message="Application generation started"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_generation(
    project_id: str,
    requirements: str,
    tech_stack: Optional[List[str]],
    deployment_target: str,
    options: Optional[Dict[str, Any]]
):
    """Background task for running the generation"""
    try:
        # Update status
        active_projects[project_id]["status"] = "running"
        active_projects[project_id]["updated_at"] = datetime.now().isoformat()
        
        # Enhance requirements
        enhanced_requirements = requirements
        if tech_stack:
            enhanced_requirements += f"\n\nPreferred tech stack: {', '.join(tech_stack)}"
        enhanced_requirements += f"\n\nDeployment target: {deployment_target}"
        
        # Run generation
        result = factory.generate_application(enhanced_requirements)
        
        # Update status
        active_projects[project_id].update({
            "status": "completed",
            "stage": "Complete",
            "progress": 1.0,
            "result": result,
            "updated_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        active_projects[project_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        })


@app.get("/projects/{project_id}/status", response_model=ProjectStatus)
async def get_project_status(project_id: str):
    """Get the status of a specific project"""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = active_projects[project_id]
    return ProjectStatus(
        project_id=project_id,
        status=project["status"],
        stage=project["stage"],
        progress=project["progress"],
        started_at=project["started_at"],
        updated_at=project["updated_at"]
    )


@app.get("/projects/{project_id}/stream")
async def stream_project_progress(project_id: str):
    """Stream real-time progress updates for a project"""
    if project_id not in active_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    async def event_generator():
        """Generate server-sent events"""
        while True:
            if project_id in active_projects:
                project = active_projects[project_id]
                yield f"data: {json.dumps(project)}\n\n"
                
                # Stop if completed or failed
                if project["status"] in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.get("/projects", response_model=List[Dict[str, Any]])
async def list_projects():
    """List all projects"""
    projects_dir = SystemConfig.PROJECTS_DIR
    projects = []
    
    if projects_dir.exists():
        for project_path in projects_dir.iterdir():
            if project_path.is_dir():
                result_file = project_path / "project_result.json"
                if result_file.exists():
                    with open(result_file, 'r') as f:
                        project_data = json.load(f)
                        projects.append(project_data)
    
    return sorted(projects, key=lambda x: x.get('timestamp', ''), reverse=True)


@app.get("/projects/{project_id}")
async def get_project_details(project_id: str):
    """Get detailed information about a project"""
    project_dir = SystemConfig.PROJECTS_DIR / project_id
    result_file = project_dir / "project_result.json"
    
    if not result_file.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    with open(result_file, 'r') as f:
        project_data = json.load(f)
    
    return project_data


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    project_dir = SystemConfig.PROJECTS_DIR / project_id
    
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Remove from active projects
    if project_id in active_projects:
        del active_projects[project_id]
    
    # Delete directory
    import shutil
    shutil.rmtree(project_dir)
    
    return {"message": f"Project {project_id} deleted successfully"}


@app.get("/teams")
async def list_teams():
    """List all agent teams"""
    return {
        "teams": [
            {
                "id": "pdt",
                "name": "Product Definition Team",
                "description": "Transform requirements into technical specifications",
                "agents": 5
            },
            {
                "id": "dt",
                "name": "Development Team",
                "description": "Build complete full-stack application",
                "agents": 7
            },
            {
                "id": "qst",
                "name": "Quality & Security Team",
                "description": "Test and validate application",
                "agents": 6
            },
            {
                "id": "dot",
                "name": "Deployment & Operations Team",
                "description": "Deploy to production",
                "agents": 7
            },
            {
                "id": "cit",
                "name": "Continuous Improvement Team",
                "description": "Learn and improve",
                "agents": 7
            }
        ]
    }


@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    total_projects = len(list(SystemConfig.PROJECTS_DIR.iterdir())) if SystemConfig.PROJECTS_DIR.exists() else 0
    completed_projects = len([p for p in active_projects.values() if p["status"] == "completed"])
    failed_projects = len([p for p in active_projects.values() if p["status"] == "failed"])
    
    return {
        "total_projects": total_projects,
        "active_projects": len(active_projects),
        "completed_projects": completed_projects,
        "failed_projects": failed_projects,
        "success_rate": completed_projects / max(total_projects, 1) * 100,
        "uptime_seconds": (datetime.now() - start_time).total_seconds()
    }


@app.post("/workflow/validate")
async def validate_workflow(requirements: str):
    """Validate requirements before starting generation"""
    try:
        # Basic validation
        if len(requirements.strip()) < 50:
            return {
                "valid": False,
                "message": "Requirements too short. Please provide more details."
            }
        
        return {
            "valid": True,
            "message": "Requirements are valid",
            "estimated_time_minutes": 45
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== AGNO OS INTEGRATION ====================
def create_agent_os():
    """Create AgentOS instance with all teams"""
    pdt = ProductDefinitionTeam.create()
    dt = DevelopmentTeam.create()
    qst = QualitySecurityTeam.create()
    dot = DeploymentOperationsTeam.create()
    cit = ContinuousImprovementTeam.create()
    
    agent_os = AgentOS(
        agents=[],
        teams=[pdt, dt, qst, dot, cit],
        name="Autonomous Full-Stack Factory"
    )
    
    return agent_os


# ==================== MAIN ====================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "agno_os_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )