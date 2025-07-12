"""
Configuration for Scenario-CoD Testing Framework
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class TestMode(Enum):
    """Testing modes for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL_ONLY = "local_only"


@dataclass
class CoDTestConfig:
    """Configuration for CoD testing framework"""
    
    # Service URLs
    cod_service_url: str = "http://localhost:8001"
    local_models_url: str = "http://localhost:8012"
    
    # Test settings
    test_mode: TestMode = TestMode.DEVELOPMENT
    max_test_duration: int = 300  # seconds
    parallel_tests: bool = True
    cache_results: bool = True
    
    # Quality thresholds
    basic_quality_threshold: float = 0.6
    strict_quality_threshold: float = 0.8
    evidence_quality_threshold: float = 0.7
    consensus_threshold: float = 0.5
    
    # Debate settings
    max_debate_turns: int = 20
    max_argument_length: int = 500
    evidence_required: bool = True
    citation_required: bool = False
    
    # Local models configuration
    use_local_models: bool = True
    fallback_to_local: bool = True
    local_model_timeout: int = 30
    
    # Logging and monitoring
    detailed_logging: bool = True
    save_conversation_logs: bool = True
    export_metrics: bool = True
    
    # Test topics for automated testing
    test_topics: List[str] = None
    
    def __post_init__(self):
        if self.test_topics is None:
            self.test_topics = [
                "climate change policy effectiveness",
                "universal basic income implementation", 
                "artificial intelligence regulation approaches",
                "renewable energy transition strategies",
                "healthcare system reform methods",
                "education technology integration",
                "privacy vs security trade-offs",
                "economic inequality solutions",
                "sustainable urban development",
                "digital currency adoption"
            ]


# Environment-specific configurations
def get_config() -> CoDTestConfig:
    """Get configuration based on environment"""
    
    env = os.getenv("TEST_ENVIRONMENT", "development")
    
    if env == "production":
        return CoDTestConfig(
            test_mode=TestMode.PRODUCTION,
            parallel_tests=False,
            detailed_logging=False,
            basic_quality_threshold=0.8,
            strict_quality_threshold=0.9,
            max_test_duration=600
        )
    
    elif env == "staging":
        return CoDTestConfig(
            test_mode=TestMode.STAGING,
            parallel_tests=True,
            basic_quality_threshold=0.7,
            strict_quality_threshold=0.85,
            max_test_duration=450
        )
    
    elif env == "local_only":
        return CoDTestConfig(
            test_mode=TestMode.LOCAL_ONLY,
            use_local_models=True,
            cod_service_url="http://localhost:8012",  # Direct to local models
            basic_quality_threshold=0.5,  # Lower threshold for local models
            strict_quality_threshold=0.7,
            citation_required=False
        )
    
    else:  # development
        return CoDTestConfig(
            test_mode=TestMode.DEVELOPMENT,
            detailed_logging=True,
            save_conversation_logs=True,
            export_metrics=True,
            max_test_duration=300
        )


# Test scenario configurations
DEBATE_SCENARIOS = {
    "basic_two_agent": {
        "name": "Basic Two-Agent Debate",
        "description": "Test fundamental debate mechanics with two opposing agents",
        "agent_count": 2,
        "max_turns": 10,
        "quality_threshold": 0.6,
        "required_criteria": ["logical_consistency", "argument_structure"]
    },
    
    "moderated_debate": {
        "name": "Moderated Three-Agent Debate", 
        "description": "Test moderated debate with synthesis generation",
        "agent_count": 3,
        "max_turns": 15,
        "quality_threshold": 0.65,
        "required_criteria": ["logical_consistency", "consensus_building", "response_relevance"]
    },
    
    "evidence_intensive": {
        "name": "Evidence-Intensive Debate",
        "description": "Test high-standard evidence requirements",
        "agent_count": 2,
        "max_turns": 12,
        "quality_threshold": 0.8,
        "evidence_required": True,
        "citation_required": True,
        "required_criteria": ["evidence_quality", "argument_structure"]
    },
    
    "fallacy_resistance": {
        "name": "Logical Fallacy Resistance Test",
        "description": "Test agent behavior when confronted with fallacies",
        "agent_count": 1,
        "max_turns": 8,
        "quality_threshold": 0.7,
        "inject_fallacies": True,
        "required_criteria": ["fallacy_detection", "logical_consistency"]
    },
    
    "consensus_building": {
        "name": "Consensus Building Challenge",
        "description": "Test ability to work toward meaningful compromise",
        "agent_count": 3,
        "max_turns": 18,
        "quality_threshold": 0.6,
        "consensus_required": True,
        "required_criteria": ["consensus_building", "response_relevance"]
    },
    
    "local_models_only": {
        "name": "Local Models Performance Test",
        "description": "Test debate quality using only local models",
        "agent_count": 2,
        "max_turns": 10,
        "quality_threshold": 0.5,
        "use_local_only": True,
        "required_criteria": ["logical_consistency", "argument_structure"]
    }
}


# Judge criteria configurations
JUDGE_CRITERIA_CONFIGS = {
    "basic": [
        "logical_consistency",
        "argument_structure"
    ],
    
    "standard": [
        "logical_consistency", 
        "argument_structure",
        "evidence_quality",
        "response_relevance"
    ],
    
    "comprehensive": [
        "logical_consistency",
        "argument_structure", 
        "evidence_quality",
        "response_relevance",
        "fallacy_detection",
        "consensus_building"
    ],
    
    "research_grade": [
        "logical_consistency",
        "argument_structure",
        "evidence_quality", 
        "response_relevance",
        "fallacy_detection",
        "consensus_building",
        "ethical_reasoning"
    ]
}


# Model configurations for different testing scenarios
MODEL_CONFIGS = {
    "cloud_models": {
        "primary": "openai/gpt-4-turbo",
        "secondary": "anthropic/claude-3-sonnet",
        "fallback": "openai/gpt-3.5-turbo"
    },
    
    "local_models": {
        "reasoning": "qwen2.5:14b",
        "coding": "qwen2.5-coder:7b", 
        "general": "llama3.1:8b",
        "fallback": "mistral:7b"
    },
    
    "hybrid": {
        "judge": "openai/gpt-4-turbo",
        "agents": "local",
        "moderator": "anthropic/claude-3-sonnet",
        "user_sim": "local"
    }
}


# Export default configuration
DEFAULT_CONFIG = get_config()