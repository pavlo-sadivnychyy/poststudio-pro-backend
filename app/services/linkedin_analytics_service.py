import requests
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.user import User

logger = logging.getLogger(__name__)

class LinkedInAnalyticsService:
    """
    LinkedIn Analytics & Performance Tracking Service
    """
    
    def __init__(self):
        self.base_url = "https://api.linkedin.com"
    
    def get_user_posts(self, access_token: str, count: int = 50) -> List[Dict]:
        """Get user's recent posts using correct API endpoint"""
        # First get the user's profile URN
        profile_urn = self.get_user_profile_urn(access_token)
        if not profile_urn:
            return []
        
        # Use the correct endpoint for user posts
        url = f"{self.base_url}/v2/posts"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        
        params = {
            "q": "author",
            "author": profile_urn,
            "sortBy": "CREATED_TIME",
            "count": min(count, 100)  # LinkedIn limits to 100
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            logger.info(f"User posts API response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("elements", [])
            else:
                logger.error(f"Failed to get user posts: {response.status_code} {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Exception getting user posts: {e}")
            return []
    
    def get_post_statistics(self, access_token: str, post_urn: str) -> Dict:
        """Get statistics for a specific post"""
        # Use the correct endpoint for post statistics
        url = f"{self.base_url}/v2/socialActions/{post_urn}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "likeCount": data.get("likesSummary", {}).get("totalLikes", 0),
                    "commentCount": data.get("commentsSummary", {}).get("totalComments", 0),
                    "shareCount": data.get("sharesSummary", {}).get("totalShares", 0),
                    "impressionCount": data.get("impressionCount", 0),
                    "clickCount": data.get("clickCount", 0)
                }
            else:
                logger.warning(f"Could not get post stats: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.warning(f"Exception getting post stats: {e}")
            return {}
    
    def get_user_profile_urn(self, access_token: str) -> str:
        """Get user's profile URN"""
        url = f"{self.base_url}/v2/people/~"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                profile = response.json()
                return f"urn:li:person:{profile.get('id', '')}"
            return ""
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return ""
    
    def get_user_id(self, access_token: str) -> str:
        """Get user's LinkedIn ID"""
        url = f"{self.base_url}/v2/people/~"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                profile = response.json()
                return profile.get("id", "")
            return ""
        except Exception as e:
            logger.error(f"Error getting user ID: {e}")
            return ""
    
    def get_profile_analytics(self, access_token: str) -> Dict:
        """Get profile analytics data"""
        profile_urn = self.get_user_profile_urn(access_token)
        if not profile_urn:
            return {}
        
        url = f"{self.base_url}/v2/networkSizes/{profile_urn}"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "connections": data.get("firstDegreeSize", 0),
                    "followers": data.get("followerCount", 0)
                }
            return {}
        except Exception as e:
            logger.error(f"Error getting profile analytics: {e}")
            return {}
    
    # ... rest of the methods remain the same
    def analyze_post_performance(self, posts: List[Dict], post_stats: List[Dict]) -> Dict:
        """Analyze overall post performance and provide insights"""
        if not posts:
            return {"error": "No posts to analyze"}
        
        # Combine posts with their statistics
        enriched_posts = []
        for i, post in enumerate(posts):
            stats = post_stats[i] if i < len(post_stats) else {}
            
            # Extract post content properly
            content = ""
            if "content" in post:
                content = post["content"].get("text", "")
            elif "text" in post:
                content = post["text"].get("text", "") if isinstance(post["text"], dict) else str(post["text"])
            
            enriched_post = {
                "id": post.get("id", ""),
                "text": content,
                "created_time": post.get("createdTime", 0),
                "likes": stats.get("likeCount", 0),
                "comments": stats.get("commentCount", 0),
                "shares": stats.get("shareCount", 0),
                "impressions": stats.get("impressionCount", 0),
                "clicks": stats.get("clickCount", 0)
            }
            
            # Calculate engagement rate
            total_engagement = enriched_post["likes"] + enriched_post["comments"] + enriched_post["shares"]
            enriched_post["engagement_rate"] = (
                (total_engagement / enriched_post["impressions"]) * 100 
                if enriched_post["impressions"] > 0 else 0
            )
            
            enriched_posts.append(enriched_post)
        
        # Perform analysis
        total_posts = len(enriched_posts)
        total_likes = sum(p["likes"] for p in enriched_posts)
        total_comments = sum(p["comments"] for p in enriched_posts)
        total_shares = sum(p["shares"] for p in enriched_posts)
        total_impressions = sum(p["impressions"] for p in enriched_posts)
        
        avg_engagement_rate = sum(p["engagement_rate"] for p in enriched_posts) / total_posts if total_posts > 0 else 0
        
        # Find best performing post
        best_post = max(enriched_posts, key=lambda x: x["engagement_rate"]) if enriched_posts else None
        
        # Analyze posting patterns
        posting_hours = [datetime.fromtimestamp(p["created_time"] / 1000).hour for p in enriched_posts if p["created_time"]]
        best_hours = self._find_best_posting_hours(enriched_posts)
        
        return {
            "overview": {
                "total_posts": total_posts,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_impressions": total_impressions,
                "avg_engagement_rate": round(avg_engagement_rate, 2)
            },
            "best_performing_post": {
                "text": best_post["text"][:100] + "..." if best_post and len(best_post["text"]) > 100 else best_post["text"] if best_post else "",
                "engagement_rate": round(best_post["engagement_rate"], 2) if best_post else 0,
                "likes": best_post["likes"] if best_post else 0,
                "comments": best_post["comments"] if best_post else 0,
                "shares": best_post["shares"] if best_post else 0
            },
            "insights": {
                "best_posting_hours": best_hours,
                "avg_likes_per_post": round(total_likes / total_posts, 1) if total_posts > 0 else 0,
                "avg_comments_per_post": round(total_comments / total_posts, 1) if total_posts > 0 else 0,
                "engagement_trend": self._calculate_engagement_trend(enriched_posts)
            },
            "recommendations": self._generate_recommendations(enriched_posts, avg_engagement_rate)
        }
    
    def _find_best_posting_hours(self, posts: List[Dict]) -> List[int]:
        """Find the hours that generate the best engagement"""
        hour_performance = {}
        
        for post in posts:
            if post["created_time"]:
                hour = datetime.fromtimestamp(post["created_time"] / 1000).hour
                if hour not in hour_performance:
                    hour_performance[hour] = {"total_engagement": 0, "post_count": 0}
                
                total_engagement = post["likes"] + post["comments"] + post["shares"]
                hour_performance[hour]["total_engagement"] += total_engagement
                hour_performance[hour]["post_count"] += 1
        
        # Calculate average engagement per hour
        hour_averages = {}
        for hour, data in hour_performance.items():
            hour_averages[hour] = data["total_engagement"] / data["post_count"] if data["post_count"] > 0 else 0
        
        # Return top 3 hours
        sorted_hours = sorted(hour_averages.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:3]]
    
    def _calculate_engagement_trend(self, posts: List[Dict]) -> str:
        """Calculate if engagement is trending up or down"""
        if len(posts) < 2:
            return "insufficient_data"
        
        # Sort posts by creation time
        sorted_posts = sorted(posts, key=lambda x: x["created_time"])
        
        # Compare first half vs second half
        mid_point = len(sorted_posts) // 2
        first_half_avg = sum(p["engagement_rate"] for p in sorted_posts[:mid_point]) / mid_point
        second_half_avg = sum(p["engagement_rate"] for p in sorted_posts[mid_point:]) / (len(sorted_posts) - mid_point)
        
        if second_half_avg > first_half_avg * 1.1:
            return "improving"
        elif second_half_avg < first_half_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(self, posts: List[Dict], avg_engagement: float) -> List[str]:
        """Generate actionable recommendations based on performance"""
        recommendations = []
        
        if avg_engagement < 2.0:
            recommendations.append("Try posting at different times to increase engagement")
            recommendations.append("Use more engaging visuals and ask questions to encourage interaction")
        
        if avg_engagement > 5.0:
            recommendations.append("Great engagement! Keep up the current posting strategy")
            recommendations.append("Consider posting more frequently to maintain momentum")
        
        # Analyze post length
        avg_length = sum(len(p["text"]) for p in posts) / len(posts) if posts else 0
        if avg_length > 500:
            recommendations.append("Consider shorter, more concise posts for better engagement")
        elif avg_length < 100:
            recommendations.append("Try adding more context and value to your posts")
        
        return recommendations

def get_user_analytics(db: Session, user: User) -> Dict:
    """Main function to get comprehensive analytics for a user"""
    try:
        if not user.access_token:
            return {"success": False, "error": "No LinkedIn access token"}
        
        analytics_service = LinkedInAnalyticsService()
        
        # Get user's posts
        posts = analytics_service.get_user_posts(user.access_token, count=20)
        
        if not posts:
            return {
                "success": True,
                "message": "No posts found to analyze",
                "analytics": {"overview": {"total_posts": 0}}
            }
        
        # Get statistics for each post
        post_stats = []
        for post in posts:
            post_urn = post.get("id", "")
            stats = analytics_service.get_post_statistics(user.access_token, post_urn)
            post_stats.append(stats)
        
        # Get profile analytics
        profile_analytics = analytics_service.get_profile_analytics(user.access_token)
        
        # Analyze performance
        analysis = analytics_service.analyze_post_performance(posts, post_stats)
        
        # Add profile data to analysis
        analysis["profile"] = profile_analytics
        
        return {
            "success": True,
            "analytics": analysis,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics for user {user.id}: {str(e)}")
        return {"success": False, "error": str(e)}