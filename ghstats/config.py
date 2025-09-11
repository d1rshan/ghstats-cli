from pathlib import Path
import json
import os

XDG = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
CONFIG_DIR = XDG / "ghstats"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT = {
    "username": "",
    "token": "",
    "colors": ["#151B23", "#057A2E", "#30C563", "#56E879", "#8BFFAD"],
    "symbol": "⬤"
}


def ensure_config():
    """Create config directory and default config if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT, indent=2), encoding="utf-8")


def read_config():
    """Read the config file and return as dict."""
    ensure_config()
    try:
        config_text = CONFIG_FILE.read_text(encoding="utf-8")
        config = json.loads(config_text)
        
        for key, value in DEFAULT.items():
            if key not in config:
                config[key] = value
                
        return config
    except (json.JSONDecodeError, Exception) as e:
        if CONFIG_FILE.exists():
            backup_file = CONFIG_FILE.with_suffix('.json.backup')
            CONFIG_FILE.rename(backup_file)
            print(f"Warning: Config file was corrupted. Backed up to {backup_file}")
        
        CONFIG_FILE.write_text(json.dumps(DEFAULT, indent=2), encoding="utf-8")
        return DEFAULT.copy()


def write_config(username=None, token=None, colors=None, symbol=None):
    """Update the config with any provided values."""
    cfg = read_config()
    
    if username is not None:
        cfg["username"] = username
    if token is not None:
        cfg["token"] = token
    if colors is not None:
        cfg["colors"] = colors
    if symbol is not None:
        cfg["symbol"] = symbol
    
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        return cfg
    except Exception as e:
        raise RuntimeError(f"Failed to write config file: {e}")


def get_effective_config():
    """
    Return effective config with all necessary defaults.
    This ensures the application always has valid configuration values.
    """
    cfg = read_config()
    
    return {
        "username": cfg.get("username", "").strip(),
        "token": cfg.get("token", "").strip(),
        "colors": cfg.get("colors", DEFAULT["colors"]),
        "symbol": cfg.get("symbol", DEFAULT["symbol"])
    }


def is_configured():
    """Check if the basic configuration (username and token) is set up."""
    cfg = get_effective_config()
    return bool(cfg["username"] and cfg["token"])


def validate_config():
    """Validate the current configuration and return any issues found."""
    issues = []
    cfg = get_effective_config()
    
    if not cfg["username"]:
        issues.append("Username is not configured")
    
    if not cfg["token"]:
        issues.append("GitHub token is not configured")
    
    colors = cfg["colors"]
    if not isinstance(colors, list) or len(colors) != 5:
        issues.append("Colors must be a list of 5 color values")
    else:
        for i, color in enumerate(colors):
            if not isinstance(color, str) or not color.startswith("#"):
                issues.append(f"Color {i+1} must be a valid hex color (e.g., #FFFFFF)")
    
    if not isinstance(cfg["symbol"], str) or not cfg["symbol"]:
        issues.append("Symbol must be a non-empty string")
    
    return issues