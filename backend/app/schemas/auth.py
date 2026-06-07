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
