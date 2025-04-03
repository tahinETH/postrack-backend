from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.migrations import get_async_session
from db.schemas import Refinement, Inspiration
from datetime import datetime


class WorkshopRepository:
    async def save_refinement(
        self,
        user_id: str,
        tweet_draft: str,
        prompt: str,
        result: str,
        account_id: Optional[str] = None,
        additional_commands: Optional[str] = None
    ) -> None:
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_refinement = Refinement(
                user_id=user_id,
                account_id=account_id,
                tweet_draft=tweet_draft,
                additional_commands=additional_commands,
                prompt=prompt,
                result=result,
                created_at=current_timestamp
            )
            session.add(new_refinement)
            await session.commit()

    async def get_user_refinements(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(Refinement)
                .filter(Refinement.user_id == user_id)
                .order_by(Refinement.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            refinements = result.scalars().all()
            
            return [{
                'id': refinement.id,
                'user_id': refinement.user_id,
                'account_id': refinement.account_id,
                'tweet_draft': refinement.tweet_draft,
                'additional_commands': refinement.additional_commands,
                'result': refinement.result,
                'created_at': refinement.created_at
            } for refinement in refinements]

    async def save_inspiration(
        self,
        user_id: str,
        tweet_id: str,
        prompt: str,
        result: str,
        account_id: Optional[str] = None,
        is_thread: bool = False
    ) -> None:
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_inspiration = Inspiration(
                user_id=user_id,
                account_id=account_id,
                tweet_id=tweet_id,
                is_thread=is_thread,
                prompt=prompt,
                result=result,
                created_at=current_timestamp
            )
            session.add(new_inspiration)
            await session.commit()

    async def get_user_inspirations(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(Inspiration)
                .filter(Inspiration.user_id == user_id)
                .order_by(Inspiration.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            inspirations = result.scalars().all()
            
            return [{
                'id': inspiration.id,
                'user_id': inspiration.user_id,
                'account_id': inspiration.account_id,
                'tweet_id': inspiration.tweet_id,
                'is_thread': inspiration.is_thread,
                'result': inspiration.result,
                'created_at': inspiration.created_at
            } for inspiration in inspirations]
