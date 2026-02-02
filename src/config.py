from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_RAW_DIR: Path = PROJECT_ROOT / 'data' / 'raw'
    DATA_PROCESSED_DIR: Path = PROJECT_ROOT / 'data' / 'processed'

    #chunking config

    CHUNK_SIZE: int = 512 #tokens
    CHUNK_OVERLAP: int = 50 #tokens
    MAX_CODE_chunk_SIZE: int = 1000 #tokens before splitting code

    #Embedding model (for token counting)
    TOKENIZER_MODEL: str = "cl100k_base"

    class Config :
        env_file='.env'


settings = Settings()
