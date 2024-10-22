from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # Both are in sqlalchemy.orm now
from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from attributename_query import GET_MODIFIERS,GET_MODIFIER_BY_ID,CREATE_MODIFIER,UPDATE_MODIFIER,DELETE_MODIFIER, GENERATE_MODIFIER_ID
app = FastAPI()
router = APIRouter()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust as needed for security
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


Base = declarative_base()
DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


#BaseModel Class
class ModifierCreate(BaseModel):
    modifier: str
    abbreviation: str
    description: str
    isActive: bool

class ModifierUpdate(BaseModel):
    modifier: Optional[str] = None
    abbreviation: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None

class ModifierResponseData(BaseModel):
    modifier_id: str
    modifier: str
    abbreviation: str
    description: str
    isActive: bool

class ModifierResponse(BaseModel):
    message: str
    data: List[ModifierResponseData]



#All code
async def generate_modifier_id(db: AsyncSession) -> str:
    query = text(GENERATE_MODIFIER_ID)
    result = await db.execute(query)
    last_modifier_id = result.scalar()

    if last_modifier_id is not None:
        prefix, num_part = last_modifier_id.split('_')
        new_id_number = int(num_part) + 1
        return f"{prefix}_{new_id_number:04d}"  # Ensuring 4 digits format
    else:
        return "M_0001"  # Start with "M_0001" if no entries exist


# Get all noun modifiers
@router.get("/attributename", response_model=ModifierResponse)
async def get_noun_values(db: AsyncSession = Depends(get_db)):
    try:
        query = text(GET_MODIFIERS)
        result = await db.execute(query)
        rows = result.fetchall()

        return ModifierResponse(
            message="success",
            data=[ModifierResponseData(
                modifier_id=row[0],
                modifier=row[1] if row[1] is not None else "",
                abbreviation=row[3] if isinstance(row[3], str) else "",
                description=row[4] if row[4] is not None else "",
                isActive=row[2] if isinstance(row[2], bool) else True
            ) for row in rows]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/attributename/{modifier_id}", response_model=ModifierResponse)
async def get_noun(modifier_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Pass the modifier_id as a parameter
        query = text(GET_MODIFIER_BY_ID)
        result = await db.execute(query, {"modifier_id": modifier_id})
        rows = result.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Modifier not found.")

        return ModifierResponse(
            message="success",
            data=[ModifierResponseData(
                modifier_id=row[0],
                modifier=row[1] if row[1] is not None else "",
                abbreviation=str(row[3]),
                description=row[4] if row[4] is not None else "",
                isActive=bool(row[2]) if isinstance(row[2], (int, bool)) else False
            ) for row in rows]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/attributename", response_model=ModifierResponse)
async def create_noun(entry: ModifierCreate, db: AsyncSession = Depends(get_db)):
    try:
        modifier_id = await generate_modifier_id(db)
        # Ensure CREATE_MODIFIER is used correctly
        result = await db.execute(text(CREATE_MODIFIER), {
            "modifier_id": modifier_id,
            "modifier": entry.modifier,
            "abbreviation": entry.abbreviation,
            "description": entry.description,
            "isActive": entry.isActive
        })
        await db.commit()

        new_modifier = result.fetchone()
        if not new_modifier:
            raise HTTPException(status_code=500, detail="Failed to create modifier.")

        return ModifierResponse(
            message="success",
            data=[ModifierResponseData(
                modifier_id=new_modifier[0],
                modifier=new_modifier[1],
                abbreviation=new_modifier[2],
                description=new_modifier[3],
                isActive=new_modifier[4]
            )]
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate entry.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/attributename/{modifier_id}", response_model=ModifierResponse)
async def update_noun(modifier_id: str, entry: ModifierUpdate, db: AsyncSession = Depends(get_db)):
    try:
        query = text(GET_MODIFIER_BY_ID)
        result = await db.execute(query, {"modifier_id": modifier_id})
        modifier = result.fetchall()
        if not modifier:
            raise HTTPException(status_code=404, detail="Modifier not found.")

        updated_result = await db.execute(text(UPDATE_MODIFIER), {
            "modifier_id": modifier_id,
            "modifier": entry.modifier if entry.modifier is not None else modifier[1],
            "abbreviation": entry.abbreviation if entry.abbreviation is not None else modifier[2],
            "description": entry.description if entry.description is not None else modifier[3],
            "isActive": entry.isActive if entry.isActive is not None else modifier[4]
        })
        await db.commit()

        updated_modifier = updated_result.fetchone()
        if not updated_modifier:
            raise HTTPException(status_code=404, detail="Modifier not updated.")

        return ModifierResponse(
            message="success",
            data=[ModifierResponseData(
                modifier_id=updated_modifier[0],
                modifier=updated_modifier[1],
                abbreviation=updated_modifier[2],
                description=updated_modifier[3],
                isActive=bool(updated_modifier[4])
            )]
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/attributename/{modifier_id}")
async def delete_noun(modifier_id: str, db: AsyncSession = Depends(get_db)):
    try:
        query = text(GET_MODIFIER_BY_ID)
        result = await db.execute(query, {"modifier_id": modifier_id})
        modifier = result.fetchall()
        if not modifier:
            raise HTTPException(status_code=404, detail="Modifier not found.")

        await db.execute(text(DELETE_MODIFIER), {"modifier_id": modifier_id})
        await db.commit()

        return {"message": f"Modifier with ID {modifier_id} deleted successfully."}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")