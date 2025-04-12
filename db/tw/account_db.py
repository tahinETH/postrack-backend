from typing import List, Dict, Any, Optional
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.migrations import get_async_session
from db.schemas import MonitoredAccount, AccountAnalysis
from datetime import datetime


class AccountRepository():
    async def upsert_account(self, account_id: str, screen_name: str, account_details: Dict[str, Any],
                            is_active: Optional[bool] = None, update_existing: bool = True) -> None:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.account_id == account_id)
            )
            account = result.scalars().first()

            if account and update_existing:
                if is_active is not None:
                    account.is_active = is_active
                account.screen_name = screen_name
                account.account_details = json.dumps(account_details)
            elif not account:
                current_timestamp = int(datetime.now().timestamp())
                new_account = MonitoredAccount(
                    account_id=account_id,
                    screen_name=screen_name,
                    created_at=current_timestamp,
                    last_check=current_timestamp,
                    is_active=is_active if is_active is not None else True,
                    account_details=json.dumps(account_details)
                )
                session.add(new_account)
            await session.commit()

    async def stop_monitoring_account(self, account_id: str):
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.account_id == account_id)
            )
            account = result.scalars().first()
            if account:
                account.is_active = False
                await session.commit()

    async def update_account_last_check(self, account_id: str, timestamp: int):
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.account_id == account_id)
            )
            account = result.scalars().first()
            if account:
                account.last_check = timestamp
                await session.commit()

    async def get_monitored_accounts(self) -> List[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(select(MonitoredAccount))
            accounts = result.scalars().all()
            
            return [{
                'account_id': account.account_id,
                'screen_name': account.screen_name,
                'is_active': account.is_active,
                'last_check': account.last_check,
                'created_at': account.created_at,
                'account_details': json.loads(account.account_details) if account.account_details else None
            } for account in accounts]

    async def save_account_analysis(
        self, 
        user_id: str,
        account_id: str,
        top_tweets: Optional[Dict] = None,
        metrics: Optional[Dict] = None,
        quantitative_analysis: Optional[Dict] = None,
        qualitative_analysis: Optional[str] = None,
        style_analysis: Optional[Dict] = None
    ):
        current_timestamp = int(datetime.now().timestamp())
        async with get_async_session() as session:
            # Get existing analysis if it exists
            result = await session.execute(
                select(AccountAnalysis)
                .filter(
                    AccountAnalysis.account_id == account_id,
                    AccountAnalysis.user_id == user_id
                )
            )
            existing = result.scalars().first()

            if existing:
                # Update only provided fields
                if top_tweets is not None:
                    existing.top_tweets = top_tweets
                if metrics is not None:
                    existing.metrics = metrics 
                if quantitative_analysis is not None:
                    existing.quantitative_analysis = quantitative_analysis
                if qualitative_analysis is not None:
                    existing.qualitative_analysis = qualitative_analysis
                if style_analysis is not None:
                    existing.style_analysis = style_analysis
                existing.updated_at = current_timestamp
            else:
                # Create new analysis
                new_analysis = AccountAnalysis(
                    user_id=user_id,
                    account_id=account_id,
                    top_tweets=top_tweets,
                    metrics=metrics,
                    quantitative_analysis=quantitative_analysis, 
                    qualitative_analysis=qualitative_analysis,
                    style_analysis=style_analysis,
                    created_at=current_timestamp,
                    updated_at=current_timestamp
                )
                session.add(new_analysis)

            await session.commit()

    async def get_account_analysis(self, account_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(AccountAnalysis)
                .filter(
                    AccountAnalysis.account_id == account_id,
                    AccountAnalysis.user_id == user_id
                )
                .order_by(AccountAnalysis.created_at.desc())
            )
            analysis = result.scalars().first()
            
            if analysis:
                account = await self.get_account_by_id(account_id)
                
                return {
                    'id': analysis.id,
                    'account_id': analysis.account_id,
                    'top_tweets': analysis.top_tweets,
                    'metrics': analysis.metrics,
                    'quantitative_analysis': analysis.quantitative_analysis,
                    'qualitative_analysis': analysis.qualitative_analysis,
                    'style_analysis': analysis.style_analysis,
                    'created_at': analysis.created_at,
                    'updated_at': analysis.updated_at,
                    'account_details': account.get('account_details') if account else None
                }
            return None
    async def delete_account_analysis(self, user_id: str, account_id: str) -> Dict[str, Any]:
        async with get_async_session() as session:
            result = await session.execute(
                select(AccountAnalysis).filter(AccountAnalysis.user_id == user_id, AccountAnalysis.account_id == account_id)
            )
            analysis = result.scalars().first()
            
            if not analysis:
                raise ValueError(f"Account analysis with id {account_id} not found")
                
            await session.delete(analysis)
            await session.commit()
            
            return {
                "success": True,
                "id": id,
                "message": f"Account analysis with id {account_id} deleted successfully"
            }

    async def stop_all_accounts(self):
        async with get_async_session() as session:
            result = await session.execute(select(MonitoredAccount))
            accounts = result.scalars().all()
            for account in accounts:
                account.is_active = False
            await session.commit()

    async def start_all_accounts(self):
        async with get_async_session() as session:
            result = await session.execute(select(MonitoredAccount))
            accounts = result.scalars().all()
            for account in accounts:
                account.is_active = True
            await session.commit()

    async def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.account_id == account_id)
            )
            account = result.scalars().first()
            
            if account:
                return {
                    'account_id': account.account_id,
                    'screen_name': account.screen_name, 
                    'is_active': account.is_active,
                    'last_check': account.last_check,
                    'created_at': account.created_at,
                    'account_details': json.loads(account.account_details) if account.account_details else None
                }
            return None
        
    async def get_account_by_screen_name(self, screen_name: str) -> Optional[Dict[str, Any]]:
        async with get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.screen_name == screen_name)
            )
            account = result.scalars().first()
            
            if account:
                return {
                    'account_id': account.account_id,
                    'screen_name': account.screen_name, 
                    'is_active': account.is_active,
                    'last_check': account.last_check,
                    'created_at': account.created_at,
                    'account_details': json.loads(account.account_details) if account.account_details else None
                }
            return None