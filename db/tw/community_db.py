import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import select
from db.migrations import get_async_session
from db.schemas import CommunityAnalysis
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CommunityRepository:
    async def save_community_analysis(
        self, 
        user_id: str,
        community_id: str,
        status: str = None,
        error: str = None,
        tweets: Optional[Dict] = None,
        metrics: Optional[Dict] = None,
        quantitative_analysis: Optional[Dict] = None,
        qualitative_analysis: Optional[str] = None,
        style_analysis: Optional[Dict] = None,
        details: Optional[Dict] = None
    ):
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            result = await session.execute(
                select(CommunityAnalysis)
                .filter(
                    CommunityAnalysis.community_id == community_id,
                    CommunityAnalysis.user_id == user_id
                )
            )
            existing = result.scalars().first()

            if existing:
                # Update only provided fields
                if status is not None:
                    existing.status = status
                if error is not None:
                    existing.error = error
                if tweets is not None:
                    existing.top_tweets = tweets
                if metrics is not None:
                    existing.metrics = metrics 
                if quantitative_analysis is not None:
                    existing.quantitative_analysis = quantitative_analysis
                if qualitative_analysis is not None:
                    existing.qualitative_analysis = qualitative_analysis
                if style_analysis is not None:
                    existing.style_analysis = style_analysis
                if details is not None:
                    existing.details = details
                existing.updated_at = current_timestamp
            else:
                # Create new analysis
                new_analysis = CommunityAnalysis(
                    user_id=user_id,
                    community_id=community_id,
                    status=status or 'in_progress',
                    error=error if error != "" else None,
                    top_tweets=tweets if tweets != {} else None,
                    metrics=metrics if metrics != {} else None,
                    quantitative_analysis=quantitative_analysis if quantitative_analysis != {} else None,
                    qualitative_analysis=qualitative_analysis if qualitative_analysis != "" else None,
                    style_analysis=style_analysis if style_analysis != {} else None,
                    details=details if details != {} else None,
                    created_at=current_timestamp,
                    updated_at=current_timestamp
                )
                session.add(new_analysis)

            await session.commit()

    async def get_community_analysis(self, community_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CommunityAnalysis)
                .filter(
                    CommunityAnalysis.community_id == community_id,
                    CommunityAnalysis.user_id == user_id
                )
                .order_by(CommunityAnalysis.created_at.desc())
            )
            analysis = result.scalars().first()
            
            if analysis:
                return {
                    'id': analysis.id,
                    'community_id': analysis.community_id,
                    'top_tweets': analysis.top_tweets,
                    'metrics': analysis.metrics,
                    'quantitative_analysis': analysis.quantitative_analysis,
                    'qualitative_analysis': analysis.qualitative_analysis,
                    'style_analysis': analysis.style_analysis,
                    'details': analysis.details,
                    'created_at': analysis.created_at,
                    'updated_at': analysis.updated_at
                }
            return None

    async def delete_community_analysis(self, user_id: str, community_id: str) -> Dict[str, Any]:
        async with get_async_session() as session:
            result = await session.execute(
                select(CommunityAnalysis).filter(CommunityAnalysis.user_id == user_id, CommunityAnalysis.community_id == community_id)
            )
            analysis = result.scalars().first()
            
            if not analysis:
                raise ValueError(f"Community analysis with id {community_id} not found")
                
            await session.delete(analysis)
            await session.commit()
            
            return {
                "success": True,
                "id": community_id,
                "message": f"Community analysis with id {community_id} deleted successfully"
            }