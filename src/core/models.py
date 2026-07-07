from pydantic import BaseModel, Field


class GherkinStep(BaseModel):
    keyword: str
    text: str


class GherkinScenario(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)
    steps: list[GherkinStep] = Field(default_factory=list)
    examples: list[dict[str, str]] = Field(default_factory=list)
    local_metadata: dict[str, str] = Field(default_factory=dict)


class GherkinBackground(BaseModel):
    steps: list[GherkinStep] = Field(default_factory=list)


class GherkinFeature(BaseModel):
    name: str
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    background: GherkinBackground = Field(default_factory=GherkinBackground)
    scenarios: list[GherkinScenario] = Field(default_factory=list)
    global_metadata: dict[str, str] = Field(default_factory=dict)
