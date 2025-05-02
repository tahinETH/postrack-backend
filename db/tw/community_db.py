import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from db.migrations import get_async_session
from db.schemas import CommunityAnalysis
import time

logger = logging.getLogger(__name__)

class CommunityRepository:
    async def get_community_analysis(self, community_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get community analysis from database"""
        try:
            async with get_async_session() as session:
                query = select(CommunityAnalysis).where(
                    CommunityAnalysis.community_id == community_id,
                    CommunityAnalysis.user_id == user_id
                )
                result = await session.execute(query)
                analysis = result.scalar_one_or_none()

                if not analysis:
                    return None

                return {
                    "tweets": analysis.top_tweets,
                    "metrics": analysis.metrics,
                    "quantitative_analysis": analysis.quantitative_analysis,
                    "qualitative_analysis": analysis.qualitative_analysis,
                    "style_analysis": analysis.style_analysis,
                    "details": analysis.details
                }

        except Exception as e:
            logger.error(f"Error getting community analysis: {str(e)}")
            raise

    async def save_community_analysis(
        self,
        user_id: str,
        community_id: str,
        tweets: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> None:
        """Save community analysis to database"""
        try:
            current_time = int(time.time())
            async with get_async_session() as session:
                community_analysis = CommunityAnalysis(
                    user_id=user_id,
                    community_id=community_id,
                    top_tweets=tweets,
                    metrics=analysis.get("metrics"),
                    quantitative_analysis=analysis.get("quantitative_analysis"),
                    qualitative_analysis=analysis.get("qualitative_analysis"),
                    style_analysis=analysis.get("style_analysis"),
                    details=analysis.get("details"),
                    created_at=current_time,
                    updated_at=current_time
                )

                session.add(community_analysis)
                await session.commit()

        except Exception as e:
            logger.error(f"Error saving community analysis: {str(e)}")
            raise
            