from fastapi import APIRouter, HTTPException, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # Both are in sqlalchemy.orm now
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from attributevalue_query import GET_NOUNS,GET_NOUN_BY_ID,CREATE_NOUN,UPDATE_NOUN,DELETE_NOUN,GENERATE_NOUN_ID  # Import the queries
app = FastAPI()
# Initialize the router
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


#All Code operations
async def generate_noun_id(db: AsyncSession) -> str:
    query = text(GENERATE_NOUN_ID)
    result = await db.execute(query)
    last_noun_id = result.scalar()

    if last_noun_id is not None:
        prefix, num_part = last_noun_id.split('_')
        new_id_number = int(num_part) + 1
        return f"{prefix}_{new_id_number:04d}"  # Ensuring 4 digits format
    else:
        return "N_0001"  # Start with "M_0001" if no entries exist

@router.get("/attributevalue", response_model=AttributeValueResponse)
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


@router.get("/attributevalue/{noun_id}", response_model=AttributeValueResponse)
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


@router.post("/attributevalue", response_model=AttributeValueResponse)
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


@router.put("/attributevalue/{noun_id}", response_model=AttributeValueResponse)
async def update_noun(
    noun_id: str,
    noun_data: AttributeValueUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch the existing noun
        get_query = text(GENERATE_NOUN_ID)
        result = await db.execute(get_query, {'noun_id': noun_id})
        existing_noun = result.fetchone()

        if not existing_noun:
            raise HTTPException(status_code=404, detail="Noun not found")

        # Prepare the updated fields, using existing values if none are provided
        updated_noun = {
            'noun_id': noun_id,
            'noun': noun_data.noun or existing_noun[1],
            'abbreviation': noun_data.abbreviation or existing_noun[2],
            'description': noun_data.description or existing_noun[3],
            'isActive': noun_data.isActive if noun_data.isActive is not None else existing_noun[4]
        }

        # Update the noun in the database
        update_query = text(UPDATE_NOUN)
        await db.execute(update_query, updated_noun)
        await db.commit()

        # Return the updated data with full attribute mapping
        return AttributeValueResponse(
            message="Noun updated successfully",
            data=[
                AttributeValueResponseData(
                    noun_id=updated_noun['noun_id'],
                    noun=updated_noun['noun'],
                    abbreviation=updated_noun['abbreviation'],
                    description=updated_noun['description'],
                    isActive=updated_noun['isActive']
                )
            ]
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Update failed due to invalid data.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
@router.delete("/attributevalue/{noun_id}", response_model=dict)
async def delete_noun(noun_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Check if the noun exists (SELECT query)
        get_query = text(GENERATE_NOUN_ID)  # Query to fetch the noun by ID
        result = await db.execute(get_query, {'noun_id': noun_id})
        noun = result.fetchone()

        if not noun:
            raise HTTPException(status_code=404, detail="Noun not found.")

        delete_query = text(DELETE_NOUN)  # DELETE query for the noun
        await db.execute(delete_query, {'noun_id': noun_id})
        await db.commit()

        return {"message": f"Noun with ID deleted successfully."}

    except SQLAlchemyError as e:
        await db.rollback()  # Rollback in case of failure
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")




