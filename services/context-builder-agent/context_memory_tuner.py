#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Context Memory Tuner
Adaptive learning system for threshold optimization and pattern recognition
"""

import asyncio
import asyncpg
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ThresholdConfig:
    """Configuration for adaptive thresholds"""
    context_overlap_ratio: float = 0.78
    embedding_similarity: float = 0.85
    belief_consistency_index: float = 0.90
    contradiction_detection_rate: float = 0.05
    cod_activation_threshold: float = 0.3

class ThresholdOptimizationRequest(BaseModel):
    metric_name: str
    current_value: float
    target_performance: float = 0.85
    optimization_window_hours: int = 24

class ThresholdOptimizationResponse(BaseModel):
    optimized_threshold: float
    confidence: float
    expected_improvement: float
    adaptation_reason: str
    timestamp: str

class PatternAnalysisRequest(BaseModel):
    context_history: List[Dict[str, Any]]
    analysis_window_hours: int = 48

class PatternAnalysisResponse(BaseModel):
    patterns_detected: List[Dict[str, Any]]
    drift_prediction: Dict[str, Any]
    recommended_adjustments: List[Dict[str, Any]]
    timestamp: str

class ContextMemoryTuner:
    """
    Adaptive learning system that optimizes thresholds and detects patterns
    Uses machine learning to continuously improve context coherence
    """
    
    def __init__(self):
        self.app = FastAPI(title="Context Memory Tuner", version="1.0.0")
        self.db_pool = None
        self.threshold_config = ThresholdConfig()
        self.optimization_model = None
        self.pattern_detector = None
        self.performance_history = []
        self.adaptation_history = []
        self.performance_metrics = {
            "optimizations_performed": 0,
            "patterns_detected": 0,
            "threshold_adjustments": 0,
            "avg_performance_improvement": 0.0,
            "last_optimization": None
        }
        
        # Initialize FastAPI routes
        self._setup_routes()
        
        # Initialize background tasks
        asyncio.create_task(self._initialize_system())
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/optimize_threshold", response_model=ThresholdOptimizationResponse)
        async def optimize_threshold(request: ThresholdOptimizationRequest):
            """Optimize a specific threshold based on performance data"""
            try:
                result = await self._optimize_threshold(
                    request.metric_name,
                    request.current_value,
                    request.target_performance,
                    request.optimization_window_hours
                )
                
                self.performance_metrics["optimizations_performed"] += 1
                
                return ThresholdOptimizationResponse(**result)
                
            except Exception as e:
                logger.error(f"Error in threshold optimization: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/analyze_patterns", response_model=PatternAnalysisResponse)
        async def analyze_patterns(request: PatternAnalysisRequest):
            """Analyze patterns in context history"""
            try:
                result = await self._analyze_patterns(
                    request.context_history,
                    request.analysis_window_hours
                )
                
                self.performance_metrics["patterns_detected"] += len(result["patterns_detected"])
                
                return PatternAnalysisResponse(**result)
                
            except Exception as e:
                logger.error(f"Error in pattern analysis: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/current_thresholds")
        async def get_current_thresholds():
            """Get current threshold configuration"""
            return {
                "thresholds": {
                    "context_overlap_ratio": self.threshold_config.context_overlap_ratio,
                    "embedding_similarity": self.threshold_config.embedding_similarity,
                    "belief_consistency_index": self.threshold_config.belief_consistency_index,
                    "contradiction_detection_rate": self.threshold_config.contradiction_detection_rate,
                    "cod_activation_threshold": self.threshold_config.cod_activation_threshold
                },
                "last_updated": datetime.utcnow().isoformat() + "Z",
                "adaptation_count": len(self.adaptation_history)
            }
        
        @self.app.post("/apply_threshold_adjustment")
        async def apply_threshold_adjustment(metric_name: str, new_value: float, reason: str):
            """Apply threshold adjustment"""
            try:
                result = await self._apply_threshold_adjustment(metric_name, new_value, reason)
                self.performance_metrics["threshold_adjustments"] += 1
                return result
            except Exception as e:
                logger.error(f"Error applying threshold adjustment: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/adaptation_history")
        async def get_adaptation_history(limit: int = 50):
            """Get adaptation history"""
            recent_adaptations = self.adaptation_history[-limit:] if self.adaptation_history else []
            return {
                "adaptations": recent_adaptations,
                "total_count": len(self.adaptation_history),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        @self.app.get("/performance_trends")
        async def get_performance_trends():
            """Get performance trends"""
            try:
                return await self._get_performance_trends()
            except Exception as e:
                logger.error(f"Error getting performance trends: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/retrain_models")
        async def retrain_models():
            """Retrain optimization models"""
            try:
                result = await self._retrain_models()
                return result
            except Exception as e:
                logger.error(f"Error retraining models: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                db_healthy = self.db_pool is not None
                models_trained = self.optimization_model is not None
                
                return {
                    "status": "healthy" if db_healthy else "degraded",
                    "database_connected": db_healthy,
                    "models_trained": models_trained,
                    "metrics": self.performance_metrics,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get performance metrics"""
            return {
                **self.performance_metrics,
                "current_thresholds": {
                    "context_overlap_ratio": self.threshold_config.context_overlap_ratio,
                    "embedding_similarity": self.threshold_config.embedding_similarity,
                    "belief_consistency_index": self.threshold_config.belief_consistency_index,
                    "contradiction_detection_rate": self.threshold_config.contradiction_detection_rate,
                    "cod_activation_threshold": self.threshold_config.cod_activation_threshold
                },
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _initialize_system(self):
        """Initialize the memory tuner system"""
        try:
            # Initialize database connection
            await self._initialize_database()
            
            # Load historical data
            await self._load_performance_history()
            
            # Train initial models
            await self._train_initial_models()
            
            # Start background optimization loop
            asyncio.create_task(self._background_optimization_loop())
            
            logger.info("Context Memory Tuner initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Context Memory Tuner: {e}")
    
    async def _initialize_database(self):
        """Initialize database connection and tables"""
        try:
            self.db_pool = await asyncpg.create_pool(
                host="mcp-database",
                port=5432,
                database="mcp_system",
                user="mcp_user",
                password="mcp_password",  # Should come from environment
                min_size=1,
                max_size=5
            )
            
            # Create tables
            await self._create_tables()
            logger.info("Database connection established for Context Memory Tuner")
            
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            self.db_pool = None
    
    async def _create_tables(self):
        """Create necessary database tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_value FLOAT NOT NULL,
                    threshold_value FLOAT NOT NULL,
                    performance_score FLOAT,
                    context_state JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS threshold_adaptations (
                    id SERIAL PRIMARY KEY,
                    metric_name VARCHAR(100) NOT NULL,
                    old_threshold FLOAT NOT NULL,
                    new_threshold FLOAT NOT NULL,
                    reason TEXT,
                    expected_improvement FLOAT,
                    actual_improvement FLOAT,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS pattern_detections (
                    id SERIAL PRIMARY KEY,
                    pattern_type VARCHAR(100) NOT NULL,
                    pattern_description TEXT,
                    confidence FLOAT,
                    context_window JSONB,
                    timestamp TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_time 
                ON performance_metrics(metric_name, timestamp DESC);
                
                CREATE INDEX IF NOT EXISTS idx_threshold_adaptations_name_time 
                ON threshold_adaptations(metric_name, timestamp DESC);
            """)
    
    async def _load_performance_history(self):
        """Load historical performance data"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                # Load recent performance metrics
                rows = await conn.fetch("""
                    SELECT metric_name, metric_value, threshold_value, 
                           performance_score, timestamp
                    FROM performance_metrics
                    WHERE timestamp > NOW() - INTERVAL '30 days'
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)
                
                self.performance_history = [
                    {
                        "metric_name": row["metric_name"],
                        "metric_value": row["metric_value"],
                        "threshold_value": row["threshold_value"],
                        "performance_score": row["performance_score"],
                        "timestamp": row["timestamp"]
                    }
                    for row in rows
                ]
                
                # Load adaptation history
                adaptation_rows = await conn.fetch("""
                    SELECT metric_name, old_threshold, new_threshold, 
                           reason, expected_improvement, actual_improvement, timestamp
                    FROM threshold_adaptations
                    WHERE timestamp > NOW() - INTERVAL '30 days'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """)
                
                self.adaptation_history = [
                    {
                        "metric_name": row["metric_name"],
                        "old_threshold": row["old_threshold"],
                        "new_threshold": row["new_threshold"],
                        "reason": row["reason"],
                        "expected_improvement": row["expected_improvement"],
                        "actual_improvement": row["actual_improvement"],
                        "timestamp": row["timestamp"].isoformat() + "Z"
                    }
                    for row in adaptation_rows
                ]
                
                logger.info(f"Loaded {len(self.performance_history)} performance records and {len(self.adaptation_history)} adaptations")
                
        except Exception as e:
            logger.error(f"Failed to load performance history: {e}")
    
    async def _train_initial_models(self):
        """Train initial optimization models"""
        try:
            if not self.performance_history or len(self.performance_history) < 10:
                # Generate synthetic data for initial training
                await self._generate_synthetic_training_data()
            
            # Train threshold optimization model
            await self._train_optimization_model()
            
            # Train pattern detection model
            await self._train_pattern_detector()
            
            logger.info("Initial models trained successfully")
            
        except Exception as e:
            logger.error(f"Failed to train initial models: {e}")
    
    async def _generate_synthetic_training_data(self):
        """Generate synthetic training data for initial model training"""
        np.random.seed(42)
        
        metrics = ["context_overlap_ratio", "embedding_similarity", "belief_consistency_index"]
        
        for _ in range(100):
            for metric in metrics:
                # Generate realistic threshold and performance combinations
                threshold = np.random.uniform(0.5, 0.95)
                
                # Performance generally improves with higher thresholds, but with noise
                base_performance = threshold + np.random.normal(0, 0.1)
                performance = max(0.0, min(1.0, base_performance))
                
                # Add some realistic variations
                metric_value = threshold + np.random.normal(0, 0.05)
                
                self.performance_history.append({
                    "metric_name": metric,
                    "metric_value": metric_value,
                    "threshold_value": threshold,
                    "performance_score": performance,
                    "timestamp": datetime.utcnow() - timedelta(days=np.random.randint(1, 30))
                })
        
        logger.info("Generated synthetic training data")
    
    async def _train_optimization_model(self):
        """Train threshold optimization model"""
        try:
            if not self.performance_history:
                return
            
            # Prepare training data
            data = []
            for record in self.performance_history:
                if record["performance_score"] is not None:
                    data.append([
                        record["threshold_value"],
                        record["metric_value"],
                        record["performance_score"]
                    ])
            
            if len(data) < 10:
                return
            
            df = pd.DataFrame(data, columns=["threshold", "metric_value", "performance"])
            
            # Features: threshold, metric_value
            X = df[["threshold", "metric_value"]].values
            y = df["performance"].values
            
            # Train model
            self.optimization_model = RandomForestRegressor(
                n_estimators=50,
                max_depth=10,
                random_state=42
            )
            
            if len(X) > 5:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                self.optimization_model.fit(X_train, y_train)
                
                # Evaluate model
                y_pred = self.optimization_model.predict(X_test)
                r2 = r2_score(y_test, y_pred)
                logger.info(f"Optimization model trained with R² score: {r2:.3f}")
            else:
                self.optimization_model.fit(X, y)
                logger.info("Optimization model trained with limited data")
            
        except Exception as e:
            logger.error(f"Failed to train optimization model: {e}")
    
    async def _train_pattern_detector(self):
        """Train pattern detection model"""
        try:
            # Simple pattern detector based on statistical analysis
            self.pattern_detector = {
                "drift_detection": {
                    "window_size": 24,  # hours
                    "drift_threshold": 0.1,
                    "stability_threshold": 0.05
                },
                "anomaly_detection": {
                    "z_score_threshold": 2.0,
                    "percentile_threshold": 95
                }
            }
            
            logger.info("Pattern detector initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize pattern detector: {e}")
    
    async def _optimize_threshold(self, metric_name: str, current_value: float,
                                 target_performance: float, window_hours: int) -> Dict[str, Any]:
        """Optimize threshold for specific metric"""
        
        if not self.optimization_model:
            return {
                "optimized_threshold": current_value,
                "confidence": 0.0,
                "expected_improvement": 0.0,
                "adaptation_reason": "Optimization model not available",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        try:
            # Get recent performance data for this metric
            recent_data = [
                record for record in self.performance_history
                if (record["metric_name"] == metric_name and 
                    record["timestamp"] > datetime.utcnow() - timedelta(hours=window_hours))
            ]
            
            if len(recent_data) < 5:
                return {
                    "optimized_threshold": current_value,
                    "confidence": 0.0,
                    "expected_improvement": 0.0,
                    "adaptation_reason": "Insufficient data for optimization",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            
            # Calculate current performance baseline
            current_performance = np.mean([r["performance_score"] for r in recent_data if r["performance_score"]])
            
            # Test different threshold values
            test_thresholds = np.linspace(
                max(0.1, current_value - 0.2),
                min(1.0, current_value + 0.2),
                20
            )
            
            best_threshold = current_value
            best_performance = current_performance
            
            for test_threshold in test_thresholds:
                # Predict performance with this threshold
                predicted_performance = self.optimization_model.predict([[test_threshold, current_value]])[0]
                
                if predicted_performance > best_performance:
                    best_threshold = test_threshold
                    best_performance = predicted_performance
            
            # Calculate confidence based on model certainty and data quality
            confidence = min(1.0, len(recent_data) / 20) * 0.8  # Scale by data availability
            
            expected_improvement = max(0.0, best_performance - current_performance)
            
            # Generate adaptation reason
            if abs(best_threshold - current_value) < 0.01:
                reason = "Current threshold is already optimal"
            elif best_threshold > current_value:
                reason = f"Increase threshold to improve performance by {expected_improvement:.3f}"
            else:
                reason = f"Decrease threshold to improve performance by {expected_improvement:.3f}"
            
            return {
                "optimized_threshold": float(best_threshold),
                "confidence": float(confidence),
                "expected_improvement": float(expected_improvement),
                "adaptation_reason": reason,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Error in threshold optimization: {e}")
            return {
                "optimized_threshold": current_value,
                "confidence": 0.0,
                "expected_improvement": 0.0,
                "adaptation_reason": f"Optimization failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _analyze_patterns(self, context_history: List[Dict[str, Any]], 
                               window_hours: int) -> Dict[str, Any]:
        """Analyze patterns in context history"""
        
        patterns_detected = []
        
        try:
            # Drift pattern detection
            drift_patterns = await self._detect_drift_patterns(context_history, window_hours)
            patterns_detected.extend(drift_patterns)
            
            # Anomaly pattern detection
            anomaly_patterns = await self._detect_anomaly_patterns(context_history)
            patterns_detected.extend(anomaly_patterns)
            
            # Trend pattern detection
            trend_patterns = await self._detect_trend_patterns(context_history)
            patterns_detected.extend(trend_patterns)
            
            # Generate drift prediction
            drift_prediction = await self._predict_drift(context_history)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(patterns_detected, drift_prediction)
            
            return {
                "patterns_detected": patterns_detected,
                "drift_prediction": drift_prediction,
                "recommended_adjustments": recommendations,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return {
                "patterns_detected": [],
                "drift_prediction": {"risk_level": "unknown", "confidence": 0.0},
                "recommended_adjustments": [],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _detect_drift_patterns(self, context_history: List[Dict[str, Any]], 
                                   window_hours: int) -> List[Dict[str, Any]]:
        """Detect drift patterns in context history"""
        patterns = []
        
        if len(context_history) < 10:
            return patterns
        
        # Analyze coherence score drift
        coherence_scores = [item.get("coherence_score", 0.8) for item in context_history]
        if len(coherence_scores) > 5:
            recent_avg = np.mean(coherence_scores[-5:])
            older_avg = np.mean(coherence_scores[:-5])
            
            if abs(recent_avg - older_avg) > 0.1:
                patterns.append({
                    "type": "coherence_drift",
                    "description": f"Coherence score drift detected: {older_avg:.3f} -> {recent_avg:.3f}",
                    "confidence": min(1.0, abs(recent_avg - older_avg) * 5),
                    "severity": "high" if abs(recent_avg - older_avg) > 0.2 else "medium",
                    "trend": "increasing" if recent_avg > older_avg else "decreasing"
                })
        
        return patterns
    
    async def _detect_anomaly_patterns(self, context_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomaly patterns"""
        patterns = []
        
        # Check for sudden changes in context updates
        timestamps = [item.get("timestamp") for item in context_history if item.get("timestamp")]
        if len(timestamps) > 5:
            # Convert to datetime objects
            try:
                dt_timestamps = [datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps]
                intervals = [(dt_timestamps[i] - dt_timestamps[i-1]).total_seconds() / 3600 
                           for i in range(1, len(dt_timestamps))]
                
                if len(intervals) > 3:
                    avg_interval = np.mean(intervals)
                    std_interval = np.std(intervals)
                    
                    # Detect unusually long or short intervals
                    for i, interval in enumerate(intervals):
                        if abs(interval - avg_interval) > 2 * std_interval:
                            patterns.append({
                                "type": "update_frequency_anomaly",
                                "description": f"Unusual update interval detected: {interval:.1f}h vs avg {avg_interval:.1f}h",
                                "confidence": min(1.0, abs(interval - avg_interval) / (std_interval + 0.1)),
                                "severity": "medium",
                                "position": i
                            })
            except:
                pass  # Skip if timestamp parsing fails
        
        return patterns
    
    async def _detect_trend_patterns(self, context_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect trend patterns"""
        patterns = []
        
        # Analyze confidence trends
        confidences = [item.get("confidence", 0.8) for item in context_history if item.get("confidence")]
        if len(confidences) > 10:
            # Simple linear trend detection
            x = np.arange(len(confidences))
            y = np.array(confidences)
            
            # Calculate correlation coefficient as trend indicator
            correlation = np.corrcoef(x, y)[0, 1]
            
            if abs(correlation) > 0.5:
                trend_direction = "increasing" if correlation > 0 else "decreasing"
                patterns.append({
                    "type": "confidence_trend",
                    "description": f"Strong {trend_direction} trend in confidence scores",
                    "confidence": abs(correlation),
                    "severity": "medium" if abs(correlation) > 0.7 else "low",
                    "correlation": float(correlation)
                })
        
        return patterns
    
    async def _predict_drift(self, context_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict potential context drift"""
        
        if len(context_history) < 5:
            return {
                "risk_level": "unknown",
                "confidence": 0.0,
                "time_to_drift": None,
                "factors": []
            }
        
        risk_factors = []
        risk_score = 0.0
        
        # Factor 1: Recent coherence decline
        coherence_scores = [item.get("coherence_score", 0.8) for item in context_history[-5:]]
        if len(coherence_scores) >= 3:
            trend = np.mean(coherence_scores[-2:]) - np.mean(coherence_scores[:2])
            if trend < -0.05:
                risk_factors.append("declining_coherence")
                risk_score += 0.3
        
        # Factor 2: High frequency of changes
        if len(context_history) > 10:
            recent_changes = len([item for item in context_history[-5:] if item.get("mutation_applied")])
            if recent_changes > 3:
                risk_factors.append("high_change_frequency")
                risk_score += 0.2
        
        # Factor 3: Low confidence patterns
        low_confidence_count = len([item for item in context_history[-10:] if item.get("confidence", 1.0) < 0.6])
        if low_confidence_count > 3:
            risk_factors.append("low_confidence_pattern")
            risk_score += 0.25
        
        # Determine risk level
        if risk_score > 0.6:
            risk_level = "high"
        elif risk_score > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "confidence": min(1.0, risk_score + 0.1),
            "risk_score": risk_score,
            "factors": risk_factors,
            "time_to_drift": "24-48 hours" if risk_score > 0.6 else "72+ hours" if risk_score > 0.3 else None
        }
    
    async def _generate_recommendations(self, patterns: List[Dict[str, Any]], 
                                      drift_prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on pattern analysis"""
        recommendations = []
        
        # Based on drift prediction
        if drift_prediction.get("risk_level") == "high":
            recommendations.append({
                "type": "preventive_action",
                "priority": "high",
                "action": "immediate_coherence_validation",
                "description": "High drift risk detected. Perform immediate coherence validation.",
                "expected_impact": "prevent_drift"
            })
        
        # Based on detected patterns
        for pattern in patterns:
            if pattern["type"] == "coherence_drift" and pattern["confidence"] > 0.7:
                recommendations.append({
                    "type": "threshold_adjustment",
                    "priority": "medium",
                    "action": "adjust_coherence_threshold",
                    "description": f"Adjust coherence threshold to accommodate {pattern['trend']} trend",
                    "expected_impact": "improve_stability"
                })
            
            elif pattern["type"] == "confidence_trend" and pattern["confidence"] > 0.6:
                recommendations.append({
                    "type": "process_optimization",
                    "priority": "low",
                    "action": "review_confidence_sources",
                    "description": "Review confidence scoring to address trend",
                    "expected_impact": "improve_accuracy"
                })
        
        return recommendations
    
    async def _apply_threshold_adjustment(self, metric_name: str, new_value: float, reason: str) -> Dict[str, Any]:
        """Apply threshold adjustment"""
        
        # Get current threshold
        current_threshold = getattr(self.threshold_config, metric_name, None)
        if current_threshold is None:
            return {"success": False, "error": f"Unknown metric: {metric_name}"}
        
        # Apply adjustment
        setattr(self.threshold_config, metric_name, new_value)
        
        # Record adaptation
        adaptation = {
            "metric_name": metric_name,
            "old_threshold": current_threshold,
            "new_threshold": new_value,
            "reason": reason,
            "expected_improvement": 0.0,  # To be calculated later
            "actual_improvement": None,  # To be measured later
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        self.adaptation_history.append(adaptation)
        
        # Store in database
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO threshold_adaptations 
                        (metric_name, old_threshold, new_threshold, reason, expected_improvement)
                        VALUES ($1, $2, $3, $4, $5)
                    """, metric_name, current_threshold, new_value, reason, 0.0)
            except Exception as e:
                logger.error(f"Failed to store adaptation: {e}")
        
        logger.info(f"Threshold adjusted: {metric_name} {current_threshold} -> {new_value}")
        
        return {
            "success": True,
            "metric_name": metric_name,
            "old_threshold": current_threshold,
            "new_threshold": new_value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    async def _background_optimization_loop(self):
        """Background loop for continuous optimization"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Perform periodic optimizations
                if len(self.performance_history) > 20:
                    await self._periodic_optimization()
                
                # Retrain models periodically
                if len(self.performance_history) > 100:
                    await self._retrain_models()
                
            except Exception as e:
                logger.error(f"Error in background optimization loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry
    
    async def _periodic_optimization(self):
        """Perform periodic threshold optimization"""
        try:
            metrics_to_optimize = [
                "context_overlap_ratio",
                "embedding_similarity", 
                "belief_consistency_index"
            ]
            
            for metric in metrics_to_optimize:
                current_value = getattr(self.threshold_config, metric, 0.8)
                
                optimization_result = await self._optimize_threshold(
                    metric, current_value, 0.85, 24
                )
                
                # Apply optimization if improvement is significant
                if (optimization_result["expected_improvement"] > 0.05 and 
                    optimization_result["confidence"] > 0.6):
                    
                    await self._apply_threshold_adjustment(
                        metric,
                        optimization_result["optimized_threshold"],
                        f"Automatic optimization: {optimization_result['adaptation_reason']}"
                    )
            
            self.performance_metrics["last_optimization"] = datetime.utcnow().isoformat() + "Z"
            
        except Exception as e:
            logger.error(f"Error in periodic optimization: {e}")
    
    async def _retrain_models(self):
        """Retrain optimization models with latest data"""
        try:
            await self._train_optimization_model()
            logger.info("Models retrained successfully")
            return {"status": "retrained", "timestamp": datetime.utcnow().isoformat() + "Z"}
        except Exception as e:
            logger.error(f"Failed to retrain models: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def _get_performance_trends(self):
        """Get performance trends analysis"""
        if not self.performance_history:
            return {"trends": [], "summary": "Insufficient data"}
        
        trends = {}
        
        # Group by metric
        for record in self.performance_history:
            metric = record["metric_name"]
            if metric not in trends:
                trends[metric] = []
            trends[metric].append({
                "performance": record["performance_score"],
                "timestamp": record["timestamp"]
            })
        
        # Analyze trends for each metric
        trend_analysis = {}
        for metric, data in trends.items():
            if len(data) > 5:
                performances = [d["performance"] for d in data if d["performance"] is not None]
                if performances:
                    trend_analysis[metric] = {
                        "avg_performance": np.mean(performances),
                        "trend": "improving" if np.mean(performances[-3:]) > np.mean(performances[:3]) else "declining",
                        "stability": "stable" if np.std(performances) < 0.1 else "unstable",
                        "data_points": len(performances)
                    }
        
        return {
            "trends": trend_analysis,
            "summary": f"Analyzed {len(trend_analysis)} metrics",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# Global instance
memory_tuner = ContextMemoryTuner()

# FastAPI app instance for uvicorn
app = memory_tuner.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8026)