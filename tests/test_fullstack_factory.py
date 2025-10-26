"""
Comprehensive Test Suite for Autonomous Full-Stack Application Factory
"""

import pytest
import asyncio
from pathlib import Path
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from fullstack_agent_main import (
    SystemConfig,
    AutonomousFullStackFactory,
    ProductDefinitionTeam,
    DevelopmentTeam,
    QualitySecurityTeam,
    DeploymentOperationsTeam,
    ContinuousImprovementTeam
)

# ==================== FIXTURES ====================

@pytest.fixture(scope="session")
def setup_test_environment():
    """Setup test environment"""
    # Create test directories
    test_dir = Path("tests/temp")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Override config for testing
    SystemConfig.ARTIFACTS_DIR = test_dir / "artifacts"
    SystemConfig.PROJECTS_DIR = test_dir / "projects"
    SystemConfig.LOGS_DIR = test_dir / "logs"
    SystemConfig.DB_FILE = str(test_dir / "test.db")
    
    SystemConfig.setup_directories()
    
    yield
    
    # Cleanup
    import shutil
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def mock_agent_response():
    """Mock agent response"""
    return Mock(
        content="Test response",
        status="success"
    )


@pytest.fixture
def sample_requirements():
    """Sample application requirements"""
    return """
    Build a task management application with:
    - User authentication
    - CRUD operations for tasks
    - Real-time updates
    - Mobile responsive design
    """


# ==================== CONFIGURATION TESTS ====================

class TestSystemConfig:
    """Test system configuration"""
    
    def test_config_values(self):
        """Test configuration values are set"""
        assert SystemConfig.PRIMARY_MODEL
        assert SystemConfig.FAST_MODEL
        assert SystemConfig.REASONING_MODEL
        assert SystemConfig.MAX_ITERATIONS > 0
    
    def test_directory_setup(self, setup_test_environment):
        """Test directory creation"""
        assert SystemConfig.ARTIFACTS_DIR.exists()
        assert SystemConfig.PROJECTS_DIR.exists()
        assert SystemConfig.LOGS_DIR.exists()


# ==================== TEAM CREATION TESTS ====================

class TestTeamCreation:
    """Test agent team creation"""
    
    def test_product_definition_team_creation(self):
        """Test PDT creation"""
        team = ProductDefinitionTeam.create()
        assert team is not None
        assert team.name == "Product Definition Team"
        assert len(team.members) == 5
    
    def test_development_team_creation(self):
        """Test DT creation"""
        team = DevelopmentTeam.create()
        assert team is not None
        assert team.name == "Development Team"
        assert len(team.members) == 7
    
    def test_quality_security_team_creation(self):
        """Test QST creation"""
        team = QualitySecurityTeam.create()
        assert team is not None
        assert team.name == "Quality & Security Team"
        assert len(team.members) == 6
    
    def test_deployment_operations_team_creation(self):
        """Test DOT creation"""
        team = DeploymentOperationsTeam.create()
        assert team is not None
        assert team.name == "Deployment & Operations Team"
        assert len(team.members) == 7
    
    def test_continuous_improvement_team_creation(self):
        """Test CIT creation"""
        team = ContinuousImprovementTeam.create()
        assert team is not None
        assert team.name == "Continuous Improvement Team"
        assert len(team.members) == 7


# ==================== FACTORY TESTS ====================

class TestAutonomousFullStackFactory:
    """Test the main factory"""
    
    @patch('fullstack_agent_main.ProductDefinitionTeam.create')
    @patch('fullstack_agent_main.DevelopmentTeam.create')
    @patch('fullstack_agent_main.QualitySecurityTeam.create')
    @patch('fullstack_agent_main.DeploymentOperationsTeam.create')
    @patch('fullstack_agent_main.ContinuousImprovementTeam.create')
    def test_factory_initialization(
        self, 
        mock_cit, 
        mock_dot, 
        mock_qst, 
        mock_dt, 
        mock_pdt,
        setup_test_environment
    ):
        """Test factory initialization"""
        # Setup mocks
        mock_pdt.return_value = Mock()
        mock_dt.return_value = Mock()
        mock_qst.return_value = Mock()
        mock_dot.return_value = Mock()
        mock_cit.return_value = Mock()
        
        factory = AutonomousFullStackFactory()
        
        assert factory.pdt is not None
        assert factory.dt is not None
        assert factory.qst is not None
        assert factory.dot is not None
        assert factory.cit is not None
        assert factory.workflow is not None
    
    @patch.object(AutonomousFullStackFactory, 'workflow')
    def test_generate_application(
        self, 
        mock_workflow, 
        sample_requirements,
        setup_test_environment
    ):
        """Test application generation"""
        # Mock workflow response
        mock_workflow.run.return_value = Mock(
            content="Application generated successfully"
        )
        
        with patch('fullstack_agent_main.ProductDefinitionTeam.create'), \
             patch('fullstack_agent_main.DevelopmentTeam.create'), \
             patch('fullstack_agent_main.QualitySecurityTeam.create'), \
             patch('fullstack_agent_main.DeploymentOperationsTeam.create'), \
             patch('fullstack_agent_main.ContinuousImprovementTeam.create'):
            
            factory = AutonomousFullStackFactory()
            factory.workflow = mock_workflow
            
            result = factory.generate_application(sample_requirements)
            
            assert result['status'] == 'completed'
        assert Path(result['project_dir']).exists()
        
        # Verify project structure
        project_dir = Path(result['project_dir'])
        result_file = project_dir / "project_result.json"
        assert result_file.exists()


# ==================== API TESTS ====================

@pytest.mark.asyncio
class TestAPI:
    """Test FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from agno_os_server import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'version' in data
        assert 'uptime' in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
    
    def test_list_teams_endpoint(self, client):
        """Test list teams endpoint"""
        response = client.get("/teams")
        assert response.status_code == 200
        data = response.json()
        assert 'teams' in data
        assert len(data['teams']) == 5
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint"""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert 'total_projects' in data
        assert 'success_rate' in data
    
    def test_generate_endpoint(self, client, sample_requirements):
        """Test generate endpoint"""
        response = client.post(
            "/generate",
            json={
                "requirements": sample_requirements,
                "tech_stack": ["React", "FastAPI"],
                "deployment_target": "AWS"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert 'project_id' in data
        assert data['status'] == 'started'
    
    def test_validate_workflow_endpoint(self, client, sample_requirements):
        """Test workflow validation endpoint"""
        response = client.post(
            "/workflow/validate",
            params={"requirements": sample_requirements}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'valid' in data
        assert data['valid'] is True


# ==================== PERFORMANCE TESTS ====================

class TestPerformance:
    """Performance tests"""
    
    def test_team_creation_performance(self):
        """Test team creation is fast enough"""
        import time
        
        start = time.time()
        team = ProductDefinitionTeam.create()
        duration = time.time() - start
        
        assert duration < 5.0, "Team creation took too long"
        assert team is not None
    
    def test_factory_initialization_performance(self, setup_test_environment):
        """Test factory initialization performance"""
        import time
        
        with patch('fullstack_agent_main.ProductDefinitionTeam.create'), \
             patch('fullstack_agent_main.DevelopmentTeam.create'), \
             patch('fullstack_agent_main.QualitySecurityTeam.create'), \
             patch('fullstack_agent_main.DeploymentOperationsTeam.create'), \
             patch('fullstack_agent_main.ContinuousImprovementTeam.create'):
            
            start = time.time()
            factory = AutonomousFullStackFactory()
            duration = time.time() - start
            
            assert duration < 10.0, "Factory initialization took too long"
            assert factory is not None


# ==================== ERROR HANDLING TESTS ====================

class TestErrorHandling:
    """Test error handling"""
    
    def test_empty_requirements(self):
        """Test handling of empty requirements"""
        from fastapi.testclient import TestClient
        from agno_os_server import app
        client = TestClient(app)
        
        response = client.post(
            "/workflow/validate",
            params={"requirements": ""}
        )
        data = response.json()
        assert data['valid'] is False
    
    def test_invalid_project_id(self):
        """Test handling of invalid project ID"""
        from fastapi.testclient import TestClient
        from agno_os_server import app
        client = TestClient(app)
        
        response = client.get("/projects/invalid_id/status")
        assert response.status_code == 404
    
    def test_qa_check_with_invalid_input(self):
        """Test QA check with invalid input"""
        factory = AutonomousFullStackFactory()
        
        # Should not raise exception
        result = factory._check_qa_pass(None)
        assert result is False
        
        result = factory._check_qa_pass([])
        assert result is False


# ==================== UTILITY FUNCTIONS TESTS ====================

class TestUtilities:
    """Test utility functions"""
    
    def test_project_id_generation(self, setup_test_environment):
        """Test project ID generation is unique"""
        import time
        
        with patch('fullstack_agent_main.ProductDefinitionTeam.create'), \
             patch('fullstack_agent_main.DevelopmentTeam.create'), \
             patch('fullstack_agent_main.QualitySecurityTeam.create'), \
             patch('fullstack_agent_main.DeploymentOperationsTeam.create'), \
             patch('fullstack_agent_main.ContinuousImprovementTeam.create'):
            
            factory = AutonomousFullStackFactory()
            
            # Mock workflow
            factory.workflow = Mock()
            factory.workflow.run = Mock(return_value=Mock(content="test"))
            
            result1 = factory.generate_application("test 1")
            time.sleep(1)
            result2 = factory.generate_application("test 2")
            
            assert result1['project_id'] != result2['project_id']


# ==================== PYTEST CONFIGURATION ====================

def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require API keys"
    )


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


# ==================== TEST RUNNER ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=fullstack_agent_main", "--cov-report=html"])completed'
            assert 'project_id' in result
            assert 'project_dir' in result
            assert result['project_id'].startswith('project_')
    
    def test_check_qa_pass_with_pass_status(self):
        """Test QA pass check with PASS status"""
        factory = AutonomousFullStackFactory()
        
        # Test with string
        assert factory._check_qa_pass("QA PASSED")
        assert factory._check_qa_pass("Tests PASS")
        
        # Test with dict
        assert factory._check_qa_pass({"status": "PASS"})
    
    def test_check_qa_pass_with_fail_status(self):
        """Test QA pass check with FAIL status"""
        factory = AutonomousFullStackFactory()
        
        # Test with string
        assert not factory._check_qa_pass("QA FAILED")
        assert not factory._check_qa_pass("Tests FAIL")
        
        # Test with dict
        assert not factory._check_qa_pass({"status": "FAIL"})


# ==================== WORKFLOW TESTS ====================

class TestWorkflow:
    """Test workflow execution"""
    
    @patch('fullstack_agent_main.ProductDefinitionTeam.create')
    def test_workflow_step_execution(self, mock_pdt, setup_test_environment):
        """Test workflow step execution"""
        mock_team = Mock()
        mock_team.run.return_value = Mock(content="Step completed")
        mock_pdt.return_value = mock_team
        
        with patch('fullstack_agent_main.DevelopmentTeam.create'), \
             patch('fullstack_agent_main.QualitySecurityTeam.create'), \
             patch('fullstack_agent_main.DeploymentOperationsTeam.create'), \
             patch('fullstack_agent_main.ContinuousImprovementTeam.create'):
            
            factory = AutonomousFullStackFactory()
            
            # Verify workflow has steps
            assert factory.workflow is not None
            assert len(factory.workflow.steps) > 0


# ==================== INTEGRATION TESTS ====================

@pytest.mark.integration
class TestIntegration:
    """Integration tests (require real API keys)"""
    
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="Integration tests require --run-integration flag"
    )
    def test_end_to_end_generation(self, sample_requirements, setup_test_environment):
        """Test end-to-end application generation"""
        factory = AutonomousFullStackFactory()
        
        result = factory.generate_application(sample_requirements)
        
        assert result['status'] == '