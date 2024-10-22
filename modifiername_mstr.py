from fastapi import APIRouter, HTTPException, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from modifiername_query import (
    GENERATE_MODIFIER_ID, GET_MODIFIER_VALUES, GET_MODIFIER_BY_ID,
    CREATE_MODIFIER, UPDATE_MODIFIER, DELETE_MODIFIER
)


# FastAPI app setup
app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()


# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autocommit=False, autoflush=False)


Base = declarative_base()
# Database dependency
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Pydantic response models
class ModifierNameResponseData(BaseModel):
    modifier_id: str
    modifier: str
    abbreviation: str
    description: str
    isActive: bool

class ModifierNameResponse(BaseModel):
    message: str
    data: List[ModifierNameResponseData]

class ModifierNameCreate(BaseModel):
    modifier: str
    abbreviation: str
    description: str
    isActive: bool

class ModifierNameUpdate(BaseModel):
    modifier: Optional[str] = None
    abbreviation: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None



#All crud operations

async def generate_modifier_id(db: AsyncSession) -> str:
    query = text(GENERATE_MODIFIER_ID)
    result = await db.execute(query)
    last_noun_id = result.scalar()

    if last_noun_id is not None:
        prefix, num_part = last_noun_id.split('_')
        new_id_number = int(num_part) + 1
        return f"{prefix}_{new_id_number:04d}"
    else:
        return "M_0001"

# GET all modifiers
@router.get("/modifiers", response_model=ModifierNameResponse)
async def get_modifiers(db: AsyncSession = Depends(get_db)):
    try:
        query = text(GET_MODIFIER_VALUES)
        result = await db.execute(query)
        rows = result.fetchall()
        return ModifierNameResponse(
            message="success",
            data=[
                ModifierNameResponseData(
                    modifier_id=row[0],
                    modifier=row[1],
                    abbreviation=row[3],
                    description=row[4],
                    isActive=bool(row[2])
                ) for row in rows
            ]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/attributename/{modifier_id}", response_model=ModifierNameResponse)
async def get_noun(modifier_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Pass the modifier_id as a parameter
        query = text(GET_MODIFIER_BY_ID)
        result = await db.execute(query, {"modifier_id": modifier_id})
        rows = result.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Modifier not found.")

        return ModifierNameResponse(
            message="success",
            data=[ModifierNameResponseData(
                modifier_id=row[0],
                modifier=row[1] if row[1] is not None else "",
                abbreviation=str(row[3]),
                description=row[4] if row[4] is not None else "",
                isActive=bool(row[2]) if isinstance(row[2], (int, bool)) else False
            ) for row in rows]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# POST create a new modifier
@router.post("/modifiers", response_model=ModifierNameResponseData)
async def create_modifier(modifier_data: ModifierNameCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Generate a new modifier ID
        new_modifier_id = await generate_modifier_id(db)  # Call the function correctly

        # Create modifier query
        create_query = text(CREATE_MODIFIER)
        await db.execute(create_query, {
            'modifier_id': new_modifier_id,
            'modifier': modifier_data.modifier,
            'abbreviation': modifier_data.abbreviation,
            'description': modifier_data.description,
            'isActive': modifier_data.isActive
        })
        await db.commit()

        return ModifierNameResponseData(
            modifier_id=new_modifier_id,
            modifier=modifier_data.modifier,
            abbreviation=modifier_data.abbreviation,
            description=modifier_data.description,
            isActive=modifier_data.isActive
        )
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Modifier creation failed due to duplicate or invalid data.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))  # Handle ValueError specifically
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# PUT update an existing modifier
@router.put("/modifiers/{modifier_id}", response_model=ModifierNameResponseData)
async def update_modifier(modifier_id: str, modifier_data: ModifierNameUpdate, db: AsyncSession = Depends(get_db)):
    try:
        # Fetch existing modifier
        get_query = text(GET_MODIFIER_BY_ID)
        result = await db.execute(get_query, {'modifier_id': modifier_id})
        existing_modifier = result.fetchone()

        if not existing_modifier:
            raise HTTPException(status_code=404, detail="Modifier not found")

        # Update the modifier fields
        update_query = text(UPDATE_MODIFIER)
        await db.execute(update_query, {
            'modifier_id': modifier_id,
            'modifier': modifier_data.modifier or existing_modifier[1],
            'abbreviation': modifier_data.abbreviation or existing_modifier[2],
            'description': modifier_data.description or existing_modifier[3],
            'isActive': modifier_data.isActive if modifier_data.isActive is not None else existing_modifier[4]
        })
        await db.commit()

        return ModifierNameResponseData(
            modifier_id=modifier_id,
            modifier=modifier_data.modifier or existing_modifier[1],
            abbreviation=modifier_data.abbreviation or existing_modifier[2],
            description=modifier_data.description or existing_modifier[3],
            isActive=modifier_data.isActive if modifier_data.isActive is not None else existing_modifier[4]
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to invalid data.")
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# DELETE a modifier
@router.delete("/modifiers/{modifier_id}", response_model=dict)
async def delete_modifier(modifier_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Check if modifier exists
        get_query = text(GET_MODIFIER_BY_ID)
        result = await db.execute(get_query, {'modifier_id': modifier_id})
        existing_modifier = result.fetchone()

        if not existing_modifier:
            raise HTTPException(status_code=404, detail="Modifier not found")

        # Delete the modifier
        delete_query = text(DELETE_MODIFIER)
        await db.execute(delete_query, {'modifier_id': modifier_id})
        await db.commit()

        return {"message": "Modifier deleted successfully"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


