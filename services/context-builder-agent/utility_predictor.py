#!/usr/bin/env python3
"""
UltraMCP ContextBuilderAgent 2.0 - Utility Predictor
Predicts utility of context mutations using ML models
"""

import asyncio
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
import pickle
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UtilityPredictionRequest(BaseModel):
    mutation_data: Dict[str, Any]
    context_state: Dict[str, Any]
    historical_success_rate: float = 0.5

class UtilityPredictionResponse(BaseModel):
    utility_score: float
    confidence: float
    prediction_details: Dict[str, Any]
    model_consensus: Dict[str, Any]
    recommendation: str
    timestamp: str

class UtilityPredictor:
    """
    Predicts utility of context mutations using ensemble ML models
    Combines Random Forest and Neural Network for robust predictions
    """
    
    def __init__(self):
        self.app = FastAPI(title="Utility Predictor", version="1.0.0")
        self.rf_model = None
        self.nn_model = None
        self.scaler = StandardScaler()
        self.model_trained = False
        self.feature_names = [
            'confidence_score', 'source_credibility', 'domain_criticality',
            'change_magnitude', 'historical_success', 'context_coherence',
            'dependency_impact', 'temporal_relevance', 'evidence_quality',
            'stakeholder_alignment'
        ]
        self.models_path = "/root/ultramcp/.context/models"
        self.training_data_path = "/root/ultramcp/.context/data/training"
        self.performance_metrics = {
            "predictions_made": 0,
            "high_utility_predicted": 0,
            "model_accuracy": 0.0,
            "last_training": None
        }
        
        # Initialize FastAPI routes
        self._setup_routes()
        
        # Initialize models
        asyncio.create_task(self._initialize_models())
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/predict_utility", response_model=UtilityPredictionResponse)
        async def predict_utility(request: UtilityPredictionRequest):
            """Predict utility of a context mutation"""
            try:
                start_time = datetime.utcnow()
                
                if not self.model_trained:
                    await self._train_models()
                
                result = await self._predict_utility(
                    request.mutation_data,
                    request.context_state,
                    request.historical_success_rate
                )
                
                # Update metrics
                self.performance_metrics["predictions_made"] += 1
                if result["utility_score"] > 0.7:
                    self.performance_metrics["high_utility_predicted"] += 1
                
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                logger.info(f"Utility prediction completed in {processing_time:.2f}ms")
                
                return UtilityPredictionResponse(**result)
                
            except Exception as e:
                logger.error(f"Error in utility prediction: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/retrain_models")
        async def retrain_models():
            """Retrain ML models with latest data"""
            try:
                result = await self._train_models(force_retrain=True)
                return result
            except Exception as e:
                logger.error(f"Error in model retraining: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/model_performance")
        async def get_model_performance():
            """Get model performance metrics"""
            try:
                return await self._get_model_performance()
            except Exception as e:
                logger.error(f"Error getting model performance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/feature_importance")
        async def get_feature_importance():
            """Get feature importance from trained models"""
            try:
                if not self.model_trained or self.rf_model is None:
                    return {"error": "Models not trained"}
                
                importance = self.rf_model.feature_importances_
                features = list(zip(self.feature_names, importance))
                features.sort(key=lambda x: x[1], reverse=True)
                
                return {
                    "feature_importance": features,
                    "model_type": "random_forest",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            except Exception as e:
                logger.error(f"Error getting feature importance: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                models_loaded = self.rf_model is not None and self.nn_model is not None
                
                return {
                    "status": "healthy" if models_loaded else "initializing",
                    "models_trained": self.model_trained,
                    "models_loaded": models_loaded,
                    "feature_count": len(self.feature_names),
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
            success_rate = 0
            if self.performance_metrics["predictions_made"] > 0:
                success_rate = self.performance_metrics["high_utility_predicted"] / self.performance_metrics["predictions_made"]
            
            return {
                **self.performance_metrics,
                "high_utility_rate": success_rate,
                "models_path": self.models_path,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def _initialize_models(self):
        """Initialize ML models"""
        try:
            # Create directories if they don't exist
            os.makedirs(self.models_path, exist_ok=True)
            os.makedirs(self.training_data_path, exist_ok=True)
            
            # Try to load pre-trained models
            await self._load_models()
            
            # If no models found, train with synthetic data
            if not self.model_trained:
                logger.info("No pre-trained models found, training with synthetic data")
                await self._generate_synthetic_training_data()
                await self._train_models()
                
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    async def _load_models(self):
        """Load pre-trained models from disk"""
        try:
            rf_path = os.path.join(self.models_path, "random_forest.pkl")
            nn_path = os.path.join(self.models_path, "neural_network.pkl")
            scaler_path = os.path.join(self.models_path, "scaler.pkl")
            
            if all(os.path.exists(p) for p in [rf_path, nn_path, scaler_path]):
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
                with open(nn_path, 'rb') as f:
                    self.nn_model = pickle.load(f)
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                self.model_trained = True
                logger.info("Pre-trained models loaded successfully")
        
        except Exception as e:
            logger.warning(f"Failed to load pre-trained models: {e}")
    
    async def _save_models(self):
        """Save trained models to disk"""
        try:
            rf_path = os.path.join(self.models_path, "random_forest.pkl")
            nn_path = os.path.join(self.models_path, "neural_network.pkl")
            scaler_path = os.path.join(self.models_path, "scaler.pkl")
            
            with open(rf_path, 'wb') as f:
                pickle.dump(self.rf_model, f)
            with open(nn_path, 'wb') as f:
                pickle.dump(self.nn_model, f)
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
                
            logger.info("Models saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    async def _generate_synthetic_training_data(self):
        """Generate synthetic training data for initial model training"""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate features
        data = []
        for _ in range(n_samples):
            # Create realistic feature distributions
            confidence_score = np.random.beta(2, 2)  # 0-1, biased toward middle
            source_credibility = np.random.beta(3, 2)  # 0-1, biased toward high
            domain_criticality = np.random.choice([0.3, 0.5, 0.8], p=[0.3, 0.4, 0.3])
            change_magnitude = np.random.exponential(0.3)  # Small changes more common
            historical_success = np.random.beta(2, 2)
            context_coherence = np.random.beta(4, 2)  # Biased toward high coherence
            dependency_impact = np.random.gamma(2, 0.2)
            temporal_relevance = np.random.beta(2, 1)
            evidence_quality = np.random.beta(3, 2)
            stakeholder_alignment = np.random.beta(2, 2)
            
            features = [
                confidence_score, source_credibility, domain_criticality,
                change_magnitude, historical_success, context_coherence,
                dependency_impact, temporal_relevance, evidence_quality,
                stakeholder_alignment
            ]
            
            # Calculate utility based on weighted combination
            utility = (
                0.2 * confidence_score +
                0.15 * source_credibility +
                0.15 * domain_criticality +
                0.1 * (1 - min(change_magnitude, 1.0)) +  # Prefer smaller changes
                0.1 * historical_success +
                0.15 * context_coherence +
                0.05 * (1 - min(dependency_impact, 1.0)) +  # Prefer lower impact
                0.05 * temporal_relevance +
                0.1 * evidence_quality +
                0.05 * stakeholder_alignment
            )
            
            # Add some noise and threshold
            utility += np.random.normal(0, 0.1)
            utility = max(0, min(1, utility))
            
            # Binary classification: high utility (>0.6) vs low utility
            label = 1 if utility > 0.6 else 0
            
            data.append(features + [label, utility])
        
        # Create DataFrame
        columns = self.feature_names + ['label', 'utility_score']
        df = pd.DataFrame(data, columns=columns)
        
        # Save training data
        training_file = os.path.join(self.training_data_path, "synthetic_training_data.csv")
        df.to_csv(training_file, index=False)
        
        logger.info(f"Generated {n_samples} synthetic training samples")
        return df
    
    async def _train_models(self, force_retrain: bool = False):
        """Train ML models"""
        try:
            if self.model_trained and not force_retrain:
                return {"status": "models_already_trained"}
            
            # Load training data
            training_file = os.path.join(self.training_data_path, "synthetic_training_data.csv")
            if not os.path.exists(training_file):
                df = await self._generate_synthetic_training_data()
            else:
                df = pd.read_csv(training_file)
            
            # Prepare features and targets
            X = df[self.feature_names].values
            y = df['label'].values
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.rf_model.fit(X_train, y_train)  # RF doesn't need scaling
            
            # Train Neural Network
            self.nn_model = MLPClassifier(
                hidden_layer_sizes=(100, 50),
                max_iter=500,
                random_state=42,
                early_stopping=True,
                validation_fraction=0.1
            )
            self.nn_model.fit(X_train_scaled, y_train)
            
            # Evaluate models
            rf_pred = self.rf_model.predict(X_test)
            nn_pred = self.nn_model.predict(X_test_scaled)
            
            rf_accuracy = accuracy_score(y_test, rf_pred)
            nn_accuracy = accuracy_score(y_test, nn_pred)
            
            # Update metrics
            self.performance_metrics["model_accuracy"] = (rf_accuracy + nn_accuracy) / 2
            self.performance_metrics["last_training"] = datetime.utcnow().isoformat() + "Z"
            
            self.model_trained = True
            
            # Save models
            await self._save_models()
            
            logger.info(f"Models trained successfully - RF: {rf_accuracy:.3f}, NN: {nn_accuracy:.3f}")
            
            return {
                "status": "training_completed",
                "rf_accuracy": rf_accuracy,
                "nn_accuracy": nn_accuracy,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            raise
    
    def _extract_features(self, mutation_data: Dict[str, Any], 
                         context_state: Dict[str, Any],
                         historical_success: float) -> List[float]:
        """Extract features from mutation and context data"""
        
        # Extract confidence score
        confidence_score = mutation_data.get("confidence", 0.5)
        
        # Extract source credibility (based on source type)
        source = mutation_data.get("source", "unknown")
        source_credibility_map = {
            "user_input": 0.9,
            "meeting_transcript": 0.8,
            "document_analysis": 0.7,
            "ai_inference": 0.6,
            "system_generated": 0.5,
            "unknown": 0.3
        }
        source_credibility = source_credibility_map.get(source, 0.5)
        
        # Extract domain criticality
        domain = mutation_data.get("target_domain", "").split(".")[0]
        criticality_map = {
            "ORGANIZACION": 0.9,
            "OBJETIVOS": 0.9,
            "PAIN_POINTS": 0.9,
            "REGLAS_NEGOCIO": 0.9,
            "BUYER_PERSONAS": 0.8,
            "OFERTA": 0.8,
            "MERCADO": 0.6,
            "INSIGHTS": 0.5
        }
        domain_criticality = criticality_map.get(domain, 0.5)
        
        # Calculate change magnitude (normalized)
        old_value = mutation_data.get("previous_value")
        new_value = mutation_data.get("new_value")
        if old_value and new_value:
            if isinstance(old_value, str) and isinstance(new_value, str):
                change_magnitude = len(set(new_value.split()) - set(old_value.split())) / max(len(new_value.split()), 1)
            else:
                change_magnitude = 0.5  # Default for non-string changes
        else:
            change_magnitude = 1.0 if old_value is None else 0.5
        
        # Historical success rate
        historical_success = min(max(historical_success, 0.0), 1.0)
        
        # Context coherence (from context state)
        context_coherence = context_state.get("coherence_score", 0.8)
        
        # Dependency impact (estimated based on domain)
        dependency_impact = 0.8 if domain in ["ORGANIZACION", "OBJETIVOS"] else 0.3
        
        # Temporal relevance (how recent is the data)
        timestamp = mutation_data.get("timestamp", datetime.utcnow().isoformat())
        try:
            mutation_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            hours_old = (datetime.utcnow().replace(tzinfo=mutation_time.tzinfo) - mutation_time).total_seconds() / 3600
            temporal_relevance = max(0, 1 - hours_old / 24)  # Decay over 24 hours
        except:
            temporal_relevance = 0.5
        
        # Evidence quality (based on requires_cod_validation)
        evidence_quality = 0.9 if mutation_data.get("requires_cod_validation", False) else 0.6
        
        # Stakeholder alignment (estimated)
        stakeholder_alignment = 0.7  # Default value
        
        return [
            confidence_score, source_credibility, domain_criticality,
            change_magnitude, historical_success, context_coherence,
            dependency_impact, temporal_relevance, evidence_quality,
            stakeholder_alignment
        ]
    
    async def _predict_utility(self, mutation_data: Dict[str, Any],
                              context_state: Dict[str, Any],
                              historical_success: float) -> Dict[str, Any]:
        """Core utility prediction logic"""
        
        # Extract features
        features = self._extract_features(mutation_data, context_state, historical_success)
        features_array = np.array(features).reshape(1, -1)
        features_scaled = self.scaler.transform(features_array)
        
        # Get predictions from both models
        rf_prob = self.rf_model.predict_proba(features_array)[0]
        nn_prob = self.nn_model.predict_proba(features_scaled)[0]
        
        # Ensemble prediction (weighted average)
        rf_weight = 0.6  # Random Forest gets higher weight due to better interpretability
        nn_weight = 0.4
        
        utility_prob = rf_weight * rf_prob[1] + nn_weight * nn_prob[1]
        
        # Calculate confidence (agreement between models)
        model_agreement = 1 - abs(rf_prob[1] - nn_prob[1])
        confidence = min(utility_prob * model_agreement, 1.0)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(utility_prob, confidence, features)
        
        # Detailed prediction info
        prediction_details = {
            "extracted_features": dict(zip(self.feature_names, features)),
            "rf_prediction": float(rf_prob[1]),
            "nn_prediction": float(nn_prob[1]),
            "ensemble_weight": {"rf": rf_weight, "nn": nn_weight},
            "model_agreement": float(model_agreement)
        }
        
        model_consensus = {
            "unanimous": abs(rf_prob[1] - nn_prob[1]) < 0.1,
            "confidence_level": "high" if confidence > 0.8 else "medium" if confidence > 0.6 else "low",
            "prediction_strength": "strong" if utility_prob > 0.8 or utility_prob < 0.2 else "weak"
        }
        
        return {
            "utility_score": float(utility_prob),
            "confidence": float(confidence),
            "prediction_details": prediction_details,
            "model_consensus": model_consensus,
            "recommendation": recommendation,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    def _generate_recommendation(self, utility_score: float, confidence: float,
                               features: List[float]) -> str:
        """Generate recommendation based on prediction"""
        
        if utility_score > 0.8 and confidence > 0.7:
            return "HIGH UTILITY: Apply mutation immediately. Strong consensus from models."
        elif utility_score > 0.6 and confidence > 0.6:
            return "MEDIUM UTILITY: Consider applying mutation with validation. Monitor for conflicts."
        elif utility_score < 0.4 and confidence > 0.6:
            return "LOW UTILITY: Reject mutation. Low expected benefit."
        elif confidence < 0.5:
            return "UNCERTAIN: Models disagree. Consider Chain of Debate validation before applying."
        else:
            return "MODERATE UTILITY: Apply with caution. Monitor impact closely."
    
    async def _get_model_performance(self) -> Dict[str, Any]:
        """Get detailed model performance metrics"""
        if not self.model_trained:
            return {"error": "Models not trained"}
        
        return {
            "training_status": "completed" if self.model_trained else "pending",
            "last_training": self.performance_metrics["last_training"],
            "model_accuracy": self.performance_metrics["model_accuracy"],
            "predictions_made": self.performance_metrics["predictions_made"],
            "high_utility_rate": self.performance_metrics["high_utility_predicted"] / max(self.performance_metrics["predictions_made"], 1),
            "models": {
                "random_forest": {
                    "n_estimators": getattr(self.rf_model, 'n_estimators', None),
                    "max_depth": getattr(self.rf_model, 'max_depth', None)
                },
                "neural_network": {
                    "hidden_layers": getattr(self.nn_model, 'hidden_layer_sizes', None),
                    "max_iter": getattr(self.nn_model, 'max_iter', None)
                }
            },
            "feature_count": len(self.feature_names),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

# Global instance
predictor = UtilityPredictor()

# FastAPI app instance for uvicorn
app = predictor.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8023)