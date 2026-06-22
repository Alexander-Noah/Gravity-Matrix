from pydantic import BaseModel, EmailStr, Field


class AuthRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    id: int
    name: str
    email: str
    llm_configured: bool = False

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ProfileSummaryUser(BaseModel):
    id: int
    name: str
    email: str
    role: str


class ProfileSummaryStats(BaseModel):
    workspaceName: str
    currentProject: str
    projectProgress: int
    workflowStep: str
    selectedTemplate: str
    scriptStatus: str
    libraryCount: int
    schemaStatus: str


class ProfileSummaryRead(BaseModel):
    user: ProfileSummaryUser
    stats: ProfileSummaryStats


class ProfileLlmConfigRead(BaseModel):
    provider: str
    base_url: str
    model: str
    has_api_key: bool
    configured: bool


class ProfileLlmConfigUpdate(BaseModel):
    provider: str = Field(default="openai_compatible", max_length=80)
    base_url: str = Field(default="", max_length=500)
    model: str = Field(default="", max_length=255)
    api_key: str | None = Field(default=None, max_length=4000)


class ProfileLlmTestRequest(BaseModel):
    prompt: str = Field(default="请用一句话回复：大模型配置已连通。", min_length=1, max_length=1000)


class ProfileLlmTestResponse(BaseModel):
    ok: bool
    provider: str
    model: str
    content: str
