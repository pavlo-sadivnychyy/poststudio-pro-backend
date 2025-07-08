from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.user import User
from app.routes.profile import get_current_user
from app.services.linkedin_analytics_service import get_user_analytics, LinkedInAnalyticsService
import logging

router = APIRouter()

@router.get("/linkedin-analytics/overview")
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get comprehensive LinkedIn analytics overview"""
    try:
        result = get_user_analytics(db, current_user)
        
        if not result.get("success"):
            raise HTTPException(400, result.get("error", "Failed to get analytics"))
        
        return {
            "success": True,
            "data": result.get("analytics", {}),
            "last_updated": result.get("last_updated")
        }
        
    except Exception as e:
        logging.error(f"Error in analytics overview: {str(e)}")
        raise HTTPException(500, f"Analytics failed: {str(e)}")

@router.get("/linkedin-analytics/dashboard")
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard-ready analytics data"""
    try:
        if not current_user.access_token:
            raise HTTPException(400, "No LinkedIn access token found")
        
        result = get_user_analytics(db, current_user)
        
        if not result.get("success"):
            return {
                "overview": {
                    "total_posts": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_shares": 0,
                    "total_impressions": 0,
                    "avg_engagement_rate": 0
                },
                "insights": {
                    "best_posting_hours": [],
                    "engagement_trend": "no_data"
                },
                "recommendations": ["Connect your LinkedIn account to see analytics"]
            }
        
        analytics = result.get("analytics", {})
        
        # Format for dashboard display
        dashboard_data = {
            "overview": analytics.get("overview", {}),
            "best_performing_post": analytics.get("best_performing_post", {}),
            "insights": analytics.get("insights", {}),
            "recommendations": analytics.get("recommendations", []),
            "charts": {
                "engagement_trend": {
                    "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                    "data": [3.2, 4.1, 3.8, 4.5]  # This would be calculated from actual data
                },
                "post_performance": {
                    "labels": ["Likes", "Comments", "Shares"],
                    "data": [
                        analytics.get("overview", {}).get("total_likes", 0),
                        analytics.get("overview", {}).get("total_comments", 0),
                        analytics.get("overview", {}).get("total_shares", 0)
                    ]
                }
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        logging.error(f"Error in analytics dashboard: {str(e)}")
        raise HTTPException(500, f"Dashboard failed: {str(e)}")

@router.get("/linkedin-analytics/posts")
def get_recent_posts_analytics(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get analytics for recent posts"""
    try:
        if not current_user.access_token:
            raise HTTPException(400, "No LinkedIn access token found")
        
        analytics_service = LinkedInAnalyticsService()
        
        # Get recent posts
        posts = analytics_service.get_user_posts(current_user.access_token, count=limit)
        
        if not posts:
            return {
                "posts": [],
                "total": 0,
                "message": "No posts found"
            }
        
        # Get stats for each post and format for display
        formatted_posts = []
        for post in posts:
            post_urn = post.get("id", "")
            stats = analytics_service.get_post_statistics(current_user.access_token, post_urn)
            
            # Extract post content
            post_text = post.get("text", {}).get("text", "") if isinstance(post.get("text"), dict) else str(post.get("text", ""))
            created_time = post.get("created", {}).get("time", 0) if isinstance(post.get("created"), dict) else 0
            
            formatted_post = {
                "id": post_urn,
                "content": post_text[:200] + "..." if len(post_text) > 200 else post_text,
                "full_content": post_text,
                "created_date": created_time,
                "stats": {
                    "likes": stats.get("likeCount", 0),
                    "comments": stats.get("commentCount", 0),
                    "shares": stats.get("shareCount", 0),
                    "impressions": stats.get("impressionCount", 0),
                    "clicks": stats.get("clickCount", 0)
                }
            }
            
            # Calculate engagement rate
            total_engagement = formatted_post["stats"]["likes"] + formatted_post["stats"]["comments"] + formatted_post["stats"]["shares"]
            formatted_post["engagement_rate"] = (
                (total_engagement / formatted_post["stats"]["impressions"]) * 100 
                if formatted_post["stats"]["impressions"] > 0 else 0
            )
            
            formatted_posts.append(formatted_post)
        
        return {
            "posts": formatted_posts,
            "total": len(formatted_posts)
        }
        
    except Exception as e:
        logging.error(f"Error getting recent posts analytics: {str(e)}")
        raise HTTPException(500, f"Failed to get posts analytics: {str(e)}")

@router.get("/linkedin-analytics/insights")
def get_analytics_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed analytics insights and recommendations"""
    try:
        result = get_user_analytics(db, current_user)
        
        if not result.get("success"):
            return {
                "insights": [],
                "recommendations": ["Connect your LinkedIn account to see insights"],
                "optimal_posting_times": []
            }
        
        analytics = result.get("analytics", {})
        insights = analytics.get("insights", {})
        
        # Format insights for display
        formatted_insights = [
            {
                "title": "Best Posting Hours",
                "value": insights.get("best_posting_hours", []),
                "description": "Hours when your posts get the most engagement",
                "type": "posting_times"
            },
            {
                "title": "Average Engagement",
                "value": f"{analytics.get('overview', {}).get('avg_engagement_rate', 0)}%",
                "description": "Your average post engagement rate",
                "type": "metric"
            },
            {
                "title": "Engagement Trend",
                "value": insights.get("engagement_trend", "stable").replace("_", " ").title(),
                "description": "How your engagement has changed recently",
                "type": "trend"
            }
        ]
        
        return {
            "insights": formatted_insights,
            "recommendations": analytics.get("recommendations", []),
            "optimal_posting_times": insights.get("best_posting_hours", [])
        }
        
    except Exception as e:
        logging.error(f"Error getting analytics insights: {str(e)}")
        raise HTTPException(500, f"Failed to get insights: {str(e)}")

@router.post("/linkedin-analytics/refresh")
def refresh_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually refresh analytics data"""
    try:
        if not current_user.access_token:
            raise HTTPException(400, "No LinkedIn access token found")
        
        result = get_user_analytics(db, current_user)
        
        return {
            "success": result.get("success", False),
            "message": "Analytics refreshed successfully" if result.get("success") else "Failed to refresh analytics",
            "last_updated": result.get("last_updated"),
            "posts_analyzed": result.get("analytics", {}).get("overview", {}).get("total_posts", 0)
        }
        
    except Exception as e:
        logging.error(f"Error refreshing analytics: {str(e)}")
        raise HTTPException(500, f"Failed to refresh analytics: {str(e)}")

@router.get("/linkedin-analytics/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a quick summary of analytics for widgets/cards"""
    try:
        result = get_user_analytics(db, current_user)
        
        if not result.get("success"):
            return {
                "total_posts": 0,
                "total_engagement": 0,
                "avg_engagement_rate": 0,
                "best_post_engagement": 0,
                "trend": "no_data"
            }
        
        analytics = result.get("analytics", {})
        overview = analytics.get("overview", {})
        
        total_engagement = overview.get("total_likes", 0) + overview.get("total_comments", 0) + overview.get("total_shares", 0)
        
        return {
            "total_posts": overview.get("total_posts", 0),
            "total_engagement": total_engagement,
            "avg_engagement_rate": overview.get("avg_engagement_rate", 0),
            "best_post_engagement": analytics.get("best_performing_post", {}).get("engagement_rate", 0),
            "trend": analytics.get("insights", {}).get("engagement_trend", "stable"),
            "total_impressions": overview.get("total_impressions", 0)
        }
        
    except Exception as e:
        logging.error(f"Error getting analytics summary: {str(e)}")
        raise HTTPException(500, f"Failed to get summary: {str(e)}")