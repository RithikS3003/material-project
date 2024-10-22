import uvicorn
from fastapi import FastAPI
from modifiername_mstr import router as modifiers
from nounvalue_mstr import router as nounvalue
from attributenameproject import router as attributename
from attributevalueprojec import router as  attributevalue

app = FastAPI()
app.include_router(modifiers, prefix="/modifiers", tags=["modifiers"])
app.include_router(nounvalue, prefix="/nounvalue", tags=["nounvalue"])
app.include_router(attributename, prefix="/attributename", tags=["attributename"])
app.include_router(attributevalue, prefix="/attributevalue", tags=["attributevalue"])

if __name__ == "_main_":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

