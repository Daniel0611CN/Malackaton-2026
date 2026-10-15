import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"

try:
    # En local las credenciales se leen de un .env (nunca se sube al repositorio)
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def load_market_config(market: str = None) -> Dict[str, Any]:
    """Carga config/<market>.json. Por defecto usa la variable de entorno TARGET_MARKET."""
    market = market or os.getenv("TARGET_MARKET", "betsson_com")
    path = CONFIG_DIR / f"{market}.json"
    if not path.exists():
        raise ValueError(f"Mercado desconocido '{market}': no existe {path}")
    with open(path, encoding="utf-8") as f:
        config = json.load(f)
    # Permite apuntar a otro entorno (staging, mock local) sin tocar la config
    if os.getenv("MARKET_URL"):
        config["url"] = os.getenv("MARKET_URL")
    # Cualquier juego del proveedor: GAME_NAME="Lucky Drums 88" (nombre tal y como se ve en la tarjeta)
    if os.getenv("GAME_NAME"):
        config["game_name"] = os.getenv("GAME_NAME")
    return config


def get_credentials(config: Dict[str, Any], account: str) -> Tuple[str, str]:
    """
    Devuelve (usuario, contraseña) de la cuenta 'funded' o 'no_funds' del mercado,
    leyendo las variables de entorno indicadas en la config (GitHub Secrets en CI).
    """
    env_names = config["credentials_env"][account]
    user = os.getenv(env_names["user"])
    password = os.getenv(env_names["password"])
    if not user or not password:
        raise ValueError(
            f"Faltan credenciales: define {env_names['user']} y {env_names['password']} "
            f"en el entorno (.env en local, Secrets en GitHub Actions)."
        )
    return user, password
