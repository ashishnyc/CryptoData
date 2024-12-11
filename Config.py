from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
import os


class Settings(BaseSettings):
    bybit_api_key: str
    bybit_api_secret: str
    bybit_testnet: bool
    db_connection_string: str
    better_stack_source_token: str = "abc"
    num_of_orders_near_current_price: int = 10
    download_dir: str = os.path.join(os.getcwd(), "downloads")
    model_config = SettingsConfigDict(env_file=".env")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return dotenv_settings, file_secret_settings, init_settings, env_settings


settings = Settings()
