import os

class Settings:
    PROJECT_NAME: str = "NIS2 CyberShield Compliance Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nis2_compliance.db")
    
    # API Keys & Third Party
    SHODAN_API_KEY: str = os.getenv("SHODAN_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    
    # Scan Defaults
    DEFAULT_SCAN_TARGET: str = os.getenv("DEFAULT_SCAN_TARGET", "192.168.1.0/24")
    DEFAULT_SCAN_FREQUENCY_MINS: int = int(os.getenv("DEFAULT_SCAN_FREQUENCY_MINS", "60"))

settings = Settings()
