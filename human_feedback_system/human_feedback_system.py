# Advanced Human Feedback System for MCP
# Comprehensive feedback collection, analysis, and integration

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

class FeedbackType(Enum):
    """Types of feedback"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    CONTENT_QUALITY = "content_quality"

class FeedbackPriority(Enum):
    """Feedback priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class FeedbackStatus(Enum):
    """Feedback processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    ARCHIVED = "archived"

@dataclass
class FeedbackEntry:
    """Individual feedback entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    feedback_type: FeedbackType = FeedbackType.SUGGESTION
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    status: FeedbackStatus = FeedbackStatus.PENDING
    title: str = ""
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    confidence_score: float = 0.0
    related_component: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    responses: List[Dict] = field(default_factory=list)
    votes: Dict[str, int] = field(default_factory=lambda: {"up": 0, "down": 0})

@dataclass
class FeedbackAnalysis:
    """Analysis results for feedback"""
    sentiment_distribution: Dict[str, float] = field(default_factory=dict)
    topic_clusters: List[Dict] = field(default_factory=list)
    priority_distribution: Dict[str, int] = field(default_factory=dict)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    actionable_insights: List[str] = field(default_factory=list)
    recommendations: List[Dict] = field(default_factory=list)

class SentimentAnalyzer:
    """Analyze sentiment of feedback"""
    
    def __init__(self):
        # Simple rule-based sentiment analysis
        # In production, would use more sophisticated models
        self.positive_words = {
            'excellent', 'amazing', 'great', 'good', 'love', 'perfect', 
            'awesome', 'fantastic', 'wonderful', 'helpful', 'useful',
            'efficient', 'fast', 'easy', 'intuitive', 'smooth'
        }
        self.negative_words = {
            'terrible', 'awful', 'bad', 'hate', 'horrible', 'slow',
            'difficult', 'confusing', 'broken', 'error', 'bug',
            'frustrating', 'annoying', 'useless', 'complicated'
        }
    
    def analyze(self, text: str) -> tuple[float, float]:
        """
        Analyze sentiment of text
        Returns: (sentiment_score, confidence_score)
        """
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        total_sentiment_words = positive_count + negative_count
        
        if total_sentiment_words == 0:
            return 0.0, 0.0  # Neutral
        
        sentiment_score = (positive_count - negative_count) / len(words)
        confidence_score = total_sentiment_words / len(words)
        
        return sentiment_score, min(confidence_score, 1.0)

class TopicExtractor:
    """Extract topics from feedback using clustering"""
    
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    
    def extract_topics(self, feedback_texts: List[str]) -> List[Dict]:
        """Extract topics from feedback texts"""
        if len(feedback_texts) < self.n_clusters:
            return []
        
        try:
            # Vectorize texts
            tfidf_matrix = self.vectorizer.fit_transform(feedback_texts)
            
            # Cluster
            clusters = self.kmeans.fit_predict(tfidf_matrix)
            
            # Extract topics
            feature_names = self.vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(self.n_clusters):
                # Get top terms for this cluster
                center = self.kmeans.cluster_centers_[i]
                top_indices = center.argsort()[-10:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices]
                
                # Count feedback in this cluster
                cluster_size = sum(1 for c in clusters if c == i)
                
                topics.append({
                    "id": i,
                    "terms": top_terms,
                    "size": cluster_size,
                    "percentage": cluster_size / len(feedback_texts) * 100
                })
            
            return topics
            
        except Exception as e:
            logging.error(f"Topic extraction failed: {e}")
            return []

class FeedbackProcessor:
    """Process and analyze feedback"""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.topic_extractor = TopicExtractor()
        self.logger = logging.getLogger(__name__)
    
    async def process_feedback(self, feedback: FeedbackEntry) -> FeedbackEntry:
        """Process individual feedback entry"""
        try:
            # Analyze sentiment
            sentiment, confidence = self.sentiment_analyzer.analyze(feedback.content)
            feedback.sentiment_score = sentiment
            feedback.confidence_score = confidence
            
            # Auto-categorize based on content
            feedback.feedback_type = self._categorize_feedback(feedback.content)
            
            # Determine priority
            feedback.priority = self._determine_priority(feedback)
            
            # Extract tags
            feedback.tags = self._extract_tags(feedback.content)
            
            # Update status
            feedback.status = FeedbackStatus.ANALYZED
            
            self.logger.info(f"Processed feedback {feedback.id}: {feedback.feedback_type.value}")
            
        except Exception as e:
            self.logger.error(f"Error processing feedback {feedback.id}: {e}")
            feedback.status = FeedbackStatus.PENDING
        
        return feedback
    
    def _categorize_feedback(self, content: str) -> FeedbackType:
        """Auto-categorize feedback based on content"""
        content_lower = content.lower()
        
        # Bug report indicators
        if any(word in content_lower for word in ['bug', 'error', 'crash', 'broken', 'not working']):
            return FeedbackType.BUG_REPORT
        
        # Feature request indicators
        if any(word in content_lower for word in ['feature', 'add', 'implement', 'would like', 'suggestion']):
            return FeedbackType.FEATURE_REQUEST
        
        # Performance indicators
        if any(word in content_lower for word in ['slow', 'fast', 'performance', 'speed', 'lag']):
            return FeedbackType.PERFORMANCE
        
        # Usability indicators
        if any(word in content_lower for word in ['difficult', 'easy', 'confusing', 'intuitive', 'user']):
            return FeedbackType.USABILITY
        
        # Positive/negative sentiment
        sentiment, _ = self.sentiment_analyzer.analyze(content)
        if sentiment > 0.1:
            return FeedbackType.POSITIVE
        elif sentiment < -0.1:
            return FeedbackType.NEGATIVE
        
        return FeedbackType.SUGGESTION
    
    def _determine_priority(self, feedback: FeedbackEntry) -> FeedbackPriority:
        """Determine feedback priority"""
        content_lower = feedback.content.lower()
        
        # Critical indicators
        if any(word in content_lower for word in ['critical', 'urgent', 'crash', 'data loss', 'security']):
            return FeedbackPriority.CRITICAL
        
        # High priority indicators
        if any(word in content_lower for word in ['important', 'major', 'blocking', 'cannot']):
            return FeedbackPriority.HIGH
        
        # Bug reports are generally medium priority
        if feedback.feedback_type == FeedbackType.BUG_REPORT:
            return FeedbackPriority.MEDIUM
        
        # Feature requests are generally low priority
        if feedback.feedback_type == FeedbackType.FEATURE_REQUEST:
            return FeedbackPriority.LOW
        
        return FeedbackPriority.MEDIUM
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        content_lower = content.lower()
        tags = []
        
        # Component tags
        components = ['ui', 'api', 'database', 'auth', 'search', 'upload', 'download']
        for component in components:
            if component in content_lower:
                tags.append(component)
        
        # Action tags
        actions = ['login', 'register', 'save', 'delete', 'edit', 'create']
        for action in actions:
            if action in content_lower:
                tags.append(action)
        
        return tags

class HumanFeedbackSystem:
    """
    Comprehensive human feedback system for MCP
    Collects, analyzes, and integrates user feedback
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.feedback_storage: Dict[str, FeedbackEntry] = {}
        self.processor = FeedbackProcessor()
        self.logger = logging.getLogger(__name__)
        
        # Analytics
        self.analytics = {
            'total_feedback': 0,
            'feedback_by_type': defaultdict(int),
            'feedback_by_priority': defaultdict(int),
            'average_sentiment': 0.0,
            'response_rate': 0.0
        }
        
        # Callbacks for integration
        self.callbacks: Dict[str, List[Callable]] = defaultdict(list)
    
    async def submit_feedback(
        self, 
        content: str, 
        user_id: str = None,
        session_id: str = None,
        context: Dict = None,
        feedback_type: FeedbackType = None
    ) -> str:
        """Submit new feedback"""
        try:
            feedback = FeedbackEntry(
                user_id=user_id,
                session_id=session_id,
                content=content,
                context=context or {},
                feedback_type=feedback_type or FeedbackType.SUGGESTION
            )
            
            # Process feedback
            feedback = await self.processor.process_feedback(feedback)
            
            # Store feedback
            self.feedback_storage[feedback.id] = feedback
            
            # Update analytics
            self._update_analytics(feedback)
            
            # Trigger callbacks
            await self._trigger_callbacks('feedback_submitted', feedback)
            
            self.logger.info(f"Feedback submitted: {feedback.id}")
            return feedback.id
            
        except Exception as e:
            self.logger.error(f"Error submitting feedback: {e}")
            raise
    
    async def get_feedback(self, feedback_id: str) -> Optional[FeedbackEntry]:
        """Get feedback by ID"""
        return self.feedback_storage.get(feedback_id)
    
    async def list_feedback(
        self,
        feedback_type: FeedbackType = None,
        priority: FeedbackPriority = None,
        status: FeedbackStatus = None,
        user_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FeedbackEntry]:
        """List feedback with filters"""
        feedback_list = list(self.feedback_storage.values())
        
        # Apply filters
        if feedback_type:
            feedback_list = [f for f in feedback_list if f.feedback_type == feedback_type]
        if priority:
            feedback_list = [f for f in feedback_list if f.priority == priority]
        if status:
            feedback_list = [f for f in feedback_list if f.status == status]
        if user_id:
            feedback_list = [f for f in feedback_list if f.user_id == user_id]
        
        # Sort by timestamp (newest first)
        feedback_list.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply pagination
        return feedback_list[offset:offset + limit]
    
    async def update_feedback_status(
        self, 
        feedback_id: str, 
        status: FeedbackStatus,
        response: str = None
    ) -> bool:
        """Update feedback status"""
        try:
            feedback = self.feedback_storage.get(feedback_id)
            if not feedback:
                return False
            
            old_status = feedback.status
            feedback.status = status
            
            if response:
                feedback.responses.append({
                    "timestamp": datetime.now().isoformat(),
                    "response": response,
                    "status_change": f"{old_status.value} -> {status.value}"
                })
            
            # Trigger callbacks
            await self._trigger_callbacks('status_updated', feedback)
            
            self.logger.info(f"Feedback {feedback_id} status updated: {status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating feedback status: {e}")
            return False
    
    async def vote_feedback(self, feedback_id: str, vote_type: str, user_id: str) -> bool:
        """Vote on feedback (upvote/downvote)"""
        try:
            feedback = self.feedback_storage.get(feedback_id)
            if not feedback:
                return False
            
            if vote_type == "up":
                feedback.votes["up"] += 1
            elif vote_type == "down":
                feedback.votes["down"] += 1
            else:
                return False
            
            self.logger.info(f"Vote recorded for feedback {feedback_id}: {vote_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error voting on feedback: {e}")
            return False
    
    async def analyze_feedback(self, time_range: timedelta = None) -> FeedbackAnalysis:
        """Analyze feedback patterns and trends"""
        try:
            # Filter by time range if specified
            feedback_list = list(self.feedback_storage.values())
            if time_range:
                cutoff_time = datetime.now() - time_range
                feedback_list = [f for f in feedback_list if f.timestamp >= cutoff_time]
            
            if not feedback_list:
                return FeedbackAnalysis()
            
            analysis = FeedbackAnalysis()
            
            # Sentiment distribution
            sentiments = [f.sentiment_score for f in feedback_list]
            analysis.sentiment_distribution = {
                "positive": sum(1 for s in sentiments if s > 0.1) / len(sentiments),
                "neutral": sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments),
                "negative": sum(1 for s in sentiments if s < -0.1) / len(sentiments),
                "average": sum(sentiments) / len(sentiments)
            }
            
            # Priority distribution
            for feedback in feedback_list:
                analysis.priority_distribution[feedback.priority.name] += 1
            
            # Topic clustering
            feedback_texts = [f.content for f in feedback_list]
            analysis.topic_clusters = self.processor.topic_extractor.extract_topics(feedback_texts)
            
            # Trend analysis
            analysis.trend_analysis = self._analyze_trends(feedback_list)
            
            # Generate insights
            analysis.actionable_insights = self._generate_insights(feedback_list, analysis)
            
            # Generate recommendations
            analysis.recommendations = self._generate_recommendations(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing feedback: {e}")
            return FeedbackAnalysis()
    
    def _analyze_trends(self, feedback_list: List[FeedbackEntry]) -> Dict[str, Any]:
        """Analyze feedback trends over time"""
        if len(feedback_list) < 2:
            return {}
        
        # Group by day
        daily_counts = defaultdict(int)
        daily_sentiment = defaultdict(list)
        
        for feedback in feedback_list:
            day = feedback.timestamp.date()
            daily_counts[day] += 1
            daily_sentiment[day].append(feedback.sentiment_score)
        
        # Calculate trends
        days = sorted(daily_counts.keys())
        if len(days) < 2:
            return {}
        
        recent_avg = sum(daily_counts[day] for day in days[-7:]) / min(7, len(days))
        older_avg = sum(daily_counts[day] for day in days[:-7]) / max(1, len(days) - 7)
        
        volume_trend = "increasing" if recent_avg > older_avg else "decreasing"
        
        # Sentiment trend
        recent_sentiment = []
        for day in days[-7:]:
            if daily_sentiment[day]:
                recent_sentiment.extend(daily_sentiment[day])
        
        older_sentiment = []
        for day in days[:-7]:
            if daily_sentiment[day]:
                older_sentiment.extend(daily_sentiment[day])
        
        sentiment_trend = "improving"
        if recent_sentiment and older_sentiment:
            recent_avg_sentiment = sum(recent_sentiment) / len(recent_sentiment)
            older_avg_sentiment = sum(older_sentiment) / len(older_sentiment)
            sentiment_trend = "improving" if recent_avg_sentiment > older_avg_sentiment else "declining"
        
        return {
            "volume_trend": volume_trend,
            "sentiment_trend": sentiment_trend,
            "daily_average": recent_avg,
            "total_days": len(days)
        }
    
    def _generate_insights(self, feedback_list: List[FeedbackEntry], analysis: FeedbackAnalysis) -> List[str]:
        """Generate actionable insights from feedback"""
        insights = []
        
        # High priority issues
        critical_feedback = [f for f in feedback_list if f.priority == FeedbackPriority.CRITICAL]
        if critical_feedback:
            insights.append(f"🚨 {len(critical_feedback)} critical issues require immediate attention")
        
        # Sentiment insights
        negative_percentage = analysis.sentiment_distribution.get("negative", 0) * 100
        if negative_percentage > 30:
            insights.append(f"⚠️ {negative_percentage:.1f}% of feedback is negative - review user experience")
        
        # Topic insights
        if analysis.topic_clusters:
            largest_cluster = max(analysis.topic_clusters, key=lambda x: x["size"])
            insights.append(f"📊 Main concern: {', '.join(largest_cluster['terms'][:3])} ({largest_cluster['percentage']:.1f}% of feedback)")
        
        # Bug reports
        bug_reports = [f for f in feedback_list if f.feedback_type == FeedbackType.BUG_REPORT]
        if len(bug_reports) > len(feedback_list) * 0.2:
            insights.append(f"🐛 High bug report rate: {len(bug_reports)} reports ({len(bug_reports)/len(feedback_list)*100:.1f}%)")
        
        return insights
    
    def _generate_recommendations(self, analysis: FeedbackAnalysis) -> List[Dict]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Priority-based recommendations
        critical_count = analysis.priority_distribution.get("CRITICAL", 0)
        if critical_count > 0:
            recommendations.append({
                "type": "immediate_action",
                "priority": "critical",
                "title": "Address Critical Issues",
                "description": f"Resolve {critical_count} critical issues immediately",
                "estimated_effort": "high"
            })
        
        # Sentiment-based recommendations
        negative_ratio = analysis.sentiment_distribution.get("negative", 0)
        if negative_ratio > 0.3:
            recommendations.append({
                "type": "user_experience",
                "priority": "high",
                "title": "Improve User Experience",
                "description": "High negative sentiment indicates UX issues",
                "estimated_effort": "medium"
            })
        
        # Topic-based recommendations
        for cluster in analysis.topic_clusters[:3]:  # Top 3 clusters
            if cluster["percentage"] > 20:
                recommendations.append({
                    "type": "feature_improvement",
                    "priority": "medium",
                    "title": f"Address {cluster['terms'][0]} Issues",
                    "description": f"Focus on {', '.join(cluster['terms'][:3])} (affects {cluster['percentage']:.1f}% of users)",
                    "estimated_effort": "medium"
                })
        
        return recommendations
    
    def _update_analytics(self, feedback: FeedbackEntry):
        """Update analytics with new feedback"""
        self.analytics['total_feedback'] += 1
        self.analytics['feedback_by_type'][feedback.feedback_type.value] += 1
        self.analytics['feedback_by_priority'][feedback.priority.name] += 1
        
        # Update average sentiment
        total_sentiment = sum(f.sentiment_score for f in self.feedback_storage.values())
        self.analytics['average_sentiment'] = total_sentiment / len(self.feedback_storage)
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for feedback events"""
        self.callbacks[event].append(callback)
    
    async def _trigger_callbacks(self, event: str, feedback: FeedbackEntry):
        """Trigger registered callbacks"""
        for callback in self.callbacks[event]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(feedback)
                else:
                    callback(feedback)
            except Exception as e:
                self.logger.error(f"Callback error for {event}: {e}")
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get current analytics"""
        return self.analytics.copy()
    
    async def export_feedback(
        self, 
        format_type: str = "json",
        filters: Dict = None
    ) -> str:
        """Export feedback data"""
        feedback_list = await self.list_feedback(**(filters or {}))
        
        if format_type == "json":
            return json.dumps([
                {
                    "id": f.id,
                    "timestamp": f.timestamp.isoformat(),
                    "type": f.feedback_type.value,
                    "priority": f.priority.name,
                    "status": f.status.value,
                    "content": f.content,
                    "sentiment": f.sentiment_score,
                    "tags": f.tags
                }
                for f in feedback_list
            ], indent=2)
        
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "ID", "Timestamp", "Type", "Priority", "Status", 
                "Content", "Sentiment", "Tags"
            ])
            
            # Data
            for f in feedback_list:
                writer.writerow([
                    f.id, f.timestamp.isoformat(), f.feedback_type.value,
                    f.priority.name, f.status.value, f.content,
                    f.sentiment_score, ",".join(f.tags)
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")

# Integration with MCP System
class MCPFeedbackIntegration:
    """Integration layer for MCP system"""
    
    def __init__(self, feedback_system: HumanFeedbackSystem):
        self.feedback_system = feedback_system
        self.logger = logging.getLogger(__name__)
        
        # Register callbacks for MCP integration
        self.feedback_system.register_callback('feedback_submitted', self._on_feedback_submitted)
        self.feedback_system.register_callback('status_updated', self._on_status_updated)
    
    async def _on_feedback_submitted(self, feedback: FeedbackEntry):
        """Handle new feedback submission"""
        # Auto-assign to relevant team/component
        if feedback.feedback_type == FeedbackType.BUG_REPORT:
            feedback.metadata['assigned_team'] = 'engineering'
        elif feedback.feedback_type == FeedbackType.FEATURE_REQUEST:
            feedback.metadata['assigned_team'] = 'product'
        elif feedback.feedback_type == FeedbackType.USABILITY:
            feedback.metadata['assigned_team'] = 'design'
        
        # Create notification for high priority feedback
        if feedback.priority in [FeedbackPriority.HIGH, FeedbackPriority.CRITICAL]:
            await self._create_notification(feedback)
    
    async def _on_status_updated(self, feedback: FeedbackEntry):
        """Handle feedback status updates"""
        # Notify user if feedback is implemented
        if feedback.status == FeedbackStatus.IMPLEMENTED and feedback.user_id:
            await self._notify_user_implementation(feedback)
    
    async def _create_notification(self, feedback: FeedbackEntry):
        """Create notification for high priority feedback"""
        # This would integrate with notification system
        self.logger.info(f"High priority feedback notification: {feedback.id}")
    
    async def _notify_user_implementation(self, feedback: FeedbackEntry):
        """Notify user that their feedback was implemented"""
        # This would integrate with user notification system
        self.logger.info(f"User notification for implemented feedback: {feedback.id}")

# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize feedback system
        feedback_system = HumanFeedbackSystem()
        
        # Initialize MCP integration
        mcp_integration = MCPFeedbackIntegration(feedback_system)
        
        # Submit some test feedback
        feedback_id1 = await feedback_system.submit_feedback(
            "The application is really slow when loading large datasets",
            user_id="user123",
            context={"page": "dashboard", "action": "data_load"}
        )
        
        feedback_id2 = await feedback_system.submit_feedback(
            "Love the new UI design! Very intuitive and clean",
            user_id="user456",
            context={"page": "home", "feature": "ui_update"}
        )
        
        feedback_id3 = await feedback_system.submit_feedback(
            "Critical bug: application crashes when uploading files over 10MB",
            user_id="user789",
            context={"page": "upload", "action": "file_upload"}
        )
        
        # Analyze feedback
        analysis = await feedback_system.analyze_feedback()
        
        print("Feedback Analysis:")
        print(f"Sentiment Distribution: {analysis.sentiment_distribution}")
        print(f"Priority Distribution: {analysis.priority_distribution}")
        print(f"Actionable Insights: {analysis.actionable_insights}")
        print(f"Recommendations: {len(analysis.recommendations)} items")
        
        # Export feedback
        export_data = await feedback_system.export_feedback(format_type="json")
        print(f"\nExported {len(feedback_system.feedback_storage)} feedback entries")
    
    # Run example
    asyncio.run(main())

