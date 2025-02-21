from typing import List, Dict, Any, Optional
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.migrations import get_async_session
from db.schemas import MonitoredAccount
from datetime import datetime


class AccountRepository():
    async def upsert_account(self, account_id: str, screen_name: str, account_details: Dict[str, Any],
                            is_active: Optional[bool] = None, update_existing: bool = True) -> None:
        async with await get_async_session() as session:
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
        async with await get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.account_id == account_id)
            )
            account = result.scalars().first()
            if account:
                account.is_active = False
                await session.commit()

    async def update_account_last_check(self, account_id: str, timestamp: int):
        async with await get_async_session() as session:
            result = await session.execute(
                select(MonitoredAccount).filter(MonitoredAccount.account_id == account_id)
            )
            account = result.scalars().first()
            if account:
                account.last_check = timestamp
                await session.commit()

    async def get_monitored_accounts(self) -> List[Dict[str, Any]]:
        async with await get_async_session() as session:
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

    async def stop_all_accounts(self):
        async with await get_async_session() as session:
            result = await session.execute(select(MonitoredAccount))
            accounts = result.scalars().all()
            for account in accounts:
                account.is_active = False
            await session.commit()

    async def start_all_accounts(self):
        async with await get_async_session() as session:
            result = await session.execute(select(MonitoredAccount))
            accounts = result.scalars().all()
            for account in accounts:
                account.is_active = True
            await session.commit()

    async def get_account_by_id(self, account_id: str) -> Optional[Dict[str, Any]]:
        async with await get_async_session() as session:
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