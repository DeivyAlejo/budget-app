from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Budget App API'
    api_v1_prefix: str = '/api/v1'
    secret_key: str = 'change-this-in-dev'
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    database_url: str = 'sqlite:///./budget_app.db'

    frontend_url: str = 'http://localhost:5173'
    cors_origins: str = 'http://localhost:5173,http://127.0.0.1:5173,http://192.168.150.15:5173'

    registration_requires_invite: bool = False
    require_admin_approval: bool = False

    # Comma-separated admin emails. Supports both ADMIN_EMAILS and ADMIN_EMAIL.
    admin_emails: str = ''
    admin_email: str = ''

    google_client_id: str = ''
    google_client_secret: str = ''
    google_redirect_uri: str = 'http://localhost:8000/api/v1/auth/google/callback'

    # Support both .env and .env.example so local setups work even if only one exists.
    model_config = SettingsConfigDict(
        env_file=('.env', '.env.example'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(',') if item.strip()]

    def admin_emails_list(self) -> list[str]:
        combined = ','.join(part for part in [self.admin_emails, self.admin_email] if part)
        return [item.strip().lower() for item in combined.split(',') if item.strip()]

    def is_admin_email(self, email: str | None) -> bool:
        if not email:
            return False
        return email.strip().lower() in set(self.admin_emails_list())


settings = Settings()
