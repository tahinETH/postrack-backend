from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.migrations import get_async_session
from db.schemas import Refinement, ReplyAndQuote, Visualization, GenerationIdeas
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

    async def save_generation(
        self,
        user_id: str,
        input: str,
        prompt: str,
        result: str,
        account_id: Optional[str] = None,
        is_thread: bool = False
    ) -> None:
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_generation = GenerationIdeas(
                user_id=user_id,
                account_id=account_id,
                input=input,
                is_thread=is_thread,
                prompt=prompt,
                result=result,
                created_at=current_timestamp
            )
            session.add(new_generation)
            await session.commit()

    async def get_user_generations(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(GenerationIdeas)
                .filter(GenerationIdeas.user_id == user_id)
                .order_by(GenerationIdeas.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            generations = result.scalars().all()
            
            return [{
                'id': generation.id,
                'user_id': generation.user_id,
                'account_id': generation.account_id,
                'input': generation.input,
                'is_thread': generation.is_thread,
                'result': generation.result,
                'created_at': generation.created_at
            } for generation in generations]

    async def save_reply(
        self,
        user_id: str,
        tweet_id: str,
        prompt: str,
        result: str,
        account_id: Optional[str] = None,
        additional_commands: Optional[str] = None
    ) -> None:
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_reply = ReplyAndQuote(
                user_id=user_id,
                account_id=account_id,
                tweet_id=tweet_id,
                additional_commands=additional_commands,
                prompt=prompt,
                result=result,
                created_at=current_timestamp
            )
            session.add(new_reply)
            await session.commit()

    async def get_user_replies(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(ReplyAndQuote)
                .filter(ReplyAndQuote.user_id == user_id)
                .order_by(ReplyAndQuote.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            replies = result.scalars().all()
            
            return [{
                'id': reply.id,
                'user_id': reply.user_id,
                'account_id': reply.account_id,
                'tweet_id': reply.tweet_id,
                'additional_commands': reply.additional_commands,
                'result': reply.result,
                'created_at': reply.created_at
            } for reply in replies]

    async def save_visualization(
        self,
        user_id: str,
        input: str,
        prompt: str,
        result: str
    ) -> None:
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            new_visualization = Visualization(
                user_id=user_id,
                input=input,
                prompt=prompt,
                result=result,
                created_at=current_timestamp
            )
            session.add(new_visualization)
            await session.commit()

    async def get_user_visualizations(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(Visualization)
                .filter(Visualization.user_id == user_id)
                .order_by(Visualization.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            visualizations = result.scalars().all()
            
            return [{
                'id': visualization.id,
                'user_id': visualization.user_id,
                'input': visualization.input,
                'result': visualization.result,
                'created_at': visualization.created_at
            } for visualization in visualizations]
