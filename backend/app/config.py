import os
from typing import List

class Settings:
    APP_NAME: str = "Screenshot-to-code API"
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # CORS
    ALLOW_ORIGINS: List[str] = (os.getenv("ALLOW_ORIGINS", "*").split(",") if os.getenv("ALLOW_ORIGINS") else ["*"])
    ALLOW_METHODS: List[str] = ["*"]
    ALLOW_HEADERS: List[str] = ["*"]

    # DSL mapping path: prefer env; else backend asset; else Bootstrap asset if present
    DSL_MAPPING_PATH_ENV: str | None = os.getenv("DSL_MAPPING_PATH")

    @staticmethod
    def resolve_dsl_mapping_path(repo_root: str) -> str:
        # If explicitly set via env, use it
        env_path = os.getenv("DSL_MAPPING_PATH")
        if env_path and os.path.exists(env_path):
            return env_path
        # Backend local asset
        backend_asset = os.path.join(repo_root, "backend", "assets", "web-dsl-mapping.json")
        if os.path.exists(backend_asset):
            return backend_asset
        # Fallback to Bootstrap location
        bootstrap_asset = os.path.join(repo_root, "Bootstrap", "compiler", "assets", "web-dsl-mapping.json")
        return bootstrap_asset

settings = Settings()
