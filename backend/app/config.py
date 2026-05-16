import os

class Settings:
    PROJECT_NAME: str = "PROJECT BOSS API"
    VERSION: str = "1.0.0"

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "project-boss-hackathon-secret-key-2024")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_PREFIX: str = os.getenv("DYNAMODB_TABLE_PREFIX", "projectboss_")

    # Bedrock
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    BEDROCK_REGION: str = os.getenv("BEDROCK_REGION", "us-east-1")

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "https://*.amplifyapp.com",
    ]

settings = Settings()
