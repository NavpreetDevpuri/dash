from pydantic import BaseModel, Field
class ResponseFormatter(BaseModel):
    """Always use this tool to structure your response to the user."""
    answer: str = Field(description="The answer to the user's question")
    followup_question: str = Field(description="A followup question the user could ask")
    temp: str = Field(description="It should always have '101' value")

from langchain_openai import ChatOpenAI

from langchain.globals import set_debug

set_debug(True)

model = ChatOpenAI(model="gpt-4o", temperature=0)

# Bind the schema to the model
model_with_structure = model.with_structured_output(ResponseFormatter)
# Invoke the model
structured_output = model_with_structure.invoke("What is the powerhouse of the cell?")
# Get back the pydantic object
print(structured_output)



