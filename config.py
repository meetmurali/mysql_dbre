"""Configuration management for MySQL DBRE Agent."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class MySQLConfig:
    """MySQL connection configuration."""

    host: str = "localhost"
    port: int = 3306
    user: str = "dbre_agent"
    password: str = ""
    database: str = "information_schema"
    ssl_disabled: bool = True
    connect_timeout: int = 10

    @classmethod
    def from_env(cls) -> "MySQLConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "dbre_agent"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            database=os.getenv("MYSQL_DATABASE", "information_schema"),
            ssl_disabled=os.getenv("MYSQL_SSL_DISABLED", "True").lower() == "true",
            connect_timeout=int(os.getenv("MYSQL_CONNECT_TIMEOUT", "10")),
        )
