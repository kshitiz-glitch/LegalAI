import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.contract import Contract
from app.schemas.contract import ContractResponse, ContractListItem
from app.services.pdf_parser import PDFParser
from app.services.agent.graph import run_contract_analysis
from app.api.deps import get_current_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contracts", tags=["contracts"])
pdf_parser = PDFParser()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def _run_analysis(contract_id: int, text: str) -> None:
    async with AsyncSessionLocal() as db:
        try:
            result = await run_contract_analysis(text)
            contract = await db.get(Contract, contract_id)
            if contract:
                contract.status = "complete"
                contract.contract_type = result["contract_type"]
                contract.overall_risk_score = result["overall_risk_score"]
                contract.summary = result["summary"]
                contract.parties = result["parties"]
                contract.key_dates = result["key_dates"]
                contract.clauses = result["clauses"]
                contract.redlines = result["redlines"]
                contract.negotiation_strategy = result["negotiation_strategy"]
                await db.commit()
        except Exception as exc:
            logger.error(
                "Analysis failed for contract_id=%s\n%s",
                contract_id,
                traceback.format_exc(),
            )
            async with AsyncSessionLocal() as err_db:
                contract = await err_db.get(Contract, contract_id)
                if contract:
                    contract.status = "error"
                    await err_db.commit()
            raise exc


@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB)")

    text, _ = pdf_parser.extract_text(content)
    if len(text.strip()) < 200:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF. The file may be scanned/image-based.",
        )

    contract = Contract(user_id=user.id, filename=file.filename, status="analyzing")
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    background_tasks.add_task(_run_analysis, contract.id, text)
    return contract


@router.get("/", response_model=List[ContractListItem])
async def list_contracts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contract)
        .where(Contract.user_id == user.id)
        .order_by(Contract.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.user_id == user.id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.delete("/{contract_id}")
async def delete_contract(
    contract_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Contract).where(Contract.id == contract_id, Contract.user_id == user.id)
    )
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    await db.delete(contract)
    await db.commit()
    return {"detail": "Deleted"}
