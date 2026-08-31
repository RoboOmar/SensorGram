from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "super_secret_robot_key"
    DATABASE_URL: str = "postgresql://neondb_owner:npg_PrJzHfmQ15kU@ep-winter-feather-aeezkrbx-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    UPLOAD_DIR: str = "uploads"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    AI_API_KEY: str = ""
    MAIL_SERVER: str = ""
    MAIL_PORT: int = 2525
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@sensorgram.local"
    MAILTRAP_API_TOKEN: str = ""
    MAILTRAP_INBOX_ID: str = ""
    RESEND_API_KEY: str = ""
    IMGBB_API_KEY: str = "636f62e6d041bb873fb620c30a8dce44"

    class Config:
        env_file = ".env"


settings = Settings()
