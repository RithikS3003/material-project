from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # Both are in sqlalchemy.orm now
from pydantic import BaseModel
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from nounvalue_query import GET_NOUNS,GET_NOUN_BY_ID,CREATE_NOUN,UPDATE_NOUN,DELETE_NOUN, GENERATE_MODIFIER_ID
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
class AttributeValueCreate(BaseModel):
    noun: str
    abbreviation: str
    description: str
    isActive: bool

class AttributeValueUpdate(BaseModel):
    noun: Optional[str] = None
    abbreviation: Optional[str] = None
    description: Optional[str] = None
    isActive: Optional[bool] = None

class AttributeValueResponseData(BaseModel):
    noun_id: str
    noun: str
    abbreviation: str
    description: str
    isActive: bool

class AttributeValueResponse(BaseModel):
    message: str
    data: List[AttributeValueResponseData]


#All code operations
async def generate_noun_id(db: AsyncSession) -> str:
    query = text(GENERATE_MODIFIER_ID)
    result = await db.execute(query)
    last_noun_id = result.scalar()

    if last_noun_id is not None:
        prefix, num_part = last_noun_id.split('_')
        new_id_number = int(num_part) + 1
        return f"{prefix}_{new_id_number:04d}"  # Ensuring 4 digits format
    else:
        return "N_0001"  # Start with "M_0001" if no entries exist


@router.get("/nounvalue", response_model=AttributeValueResponse)
async def get_noun_values(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text(GET_NOUNS))
        rows = result.fetchall()
        return AttributeValueResponse(
            message="success",
            data=[AttributeValueResponseData(
                noun_id=row[0],
                noun=row[1] if row[1] is not None else "",
                abbreviation=row[3] if isinstance(row[3], str) else "",
                description=row[4] if row[4] is not None else "",
                isActive=row[2] if isinstance(row[2], bool) else True
            ) for row in rows]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/nounvalue/{noun_id}", response_model=AttributeValueResponse)
async def get_noun(noun_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text(GET_NOUN_BY_ID), {"noun_id": noun_id})
        rows = result.fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="Noun not found.")

        return AttributeValueResponse(
            message="success",
            data=[AttributeValueResponseData(
                noun_id=row[0],
                noun=row[1] if row[1] is not None else "",
                abbreviation=str(row[3]),
                description=row[4] if row[4] is not None else "",
                isActive=bool(row[2]) if isinstance(row[2], (int, bool)) else False
            ) for row in rows]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/nounvalue", response_model=AttributeValueResponse)
async def create_noun(entry: AttributeValueCreate, db: AsyncSession = Depends(get_db)):
    try:
        noun_id = await generate_noun_id(db)
        result = await db.execute(text(CREATE_NOUN), {
            "noun_id": noun_id,
            "noun": entry.noun,
            "abbreviation": entry.abbreviation,
            "description": entry.description,
            "isActive": entry.isActive
        })
        await db.commit()

        new_noun = result.fetchone()
        if not new_noun:
            raise HTTPException(status_code=500, detail="Failed to create noun.")

        return AttributeValueResponse(
            message="success",
            data=[AttributeValueResponseData(
                noun_id=new_noun[0],
                noun=new_noun[1],
                abbreviation=new_noun[2],
                description=new_noun[3],
                isActive=new_noun[4]
            )]
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate entry.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/nounvalue/{noun_id}", response_model=AttributeValueResponse)
async def update_noun(noun_id: str, entry: AttributeValueUpdate, db: AsyncSession = Depends(get_db)):
    try:
        result_check = await db.execute(text(GET_NOUN_BY_ID), {"noun_id": noun_id})
        noun = result_check.fetchone()
        if not noun:
            raise HTTPException(status_code=404, detail="Noun not found.")

        updated_result = await db.execute(text(UPDATE_NOUN), {
            "noun_id": noun_id,
            "noun": entry.noun if entry.noun is not None else noun[1],
            "abbreviation": entry.abbreviation if entry.abbreviation is not None else noun[2],
            "description": entry.description if entry.description is not None else noun[3],
            "isActive": entry.isActive if entry.isActive is not None else noun[4]
        })
        await db.commit()

        updated_noun = updated_result.fetchone()
        if not updated_noun:
            raise HTTPException(status_code=404, detail="Noun not updated.")

        return AttributeValueResponse(
            message="success",
            data=[AttributeValueResponseData(
                noun_id=updated_noun[0],
                noun=updated_noun[1],
                abbreviation=updated_noun[2],
                description=updated_noun[3],
                isActive=bool(updated_noun[4])
            )]
        )
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/nounvalue/{noun_id}")
async def delete_noun(noun_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result_check = await db.execute(text(GET_NOUN_BY_ID), {"noun_id": noun_id})
        noun = result_check.fetchone()
        if not noun:
            raise HTTPException(status_code=404, detail="Noun not found.")

        await db.execute(text(DELETE_NOUN), {"noun_id": noun_id})
        await db.commit()

        return {"message": f"Noun with ID {noun_id} deleted successfully."}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")