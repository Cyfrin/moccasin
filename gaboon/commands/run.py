from typing import List, Any
import sys
from pathlib import Path
from gaboon.logging import logger
from gaboon.config import get_config, initialize_global_config
import importlib.util
import boa



def main(args: List[Any]) -> int:
    initialize_global_config()
    run_script(args.script_name_or_path)
    return 0

def run_script(script_name_or_path: Path | str):
    config_root = get_config().get_root()
    script_path: Path = get_script_path(script_name_or_path)

    # Set up the environment (add necessary paths to sys.path, etc.)
    sys.path.insert(0, str(config_root)) if config_root not in sys.path else None
    sys.path.insert(0, str(config_root / "src")) if (
        config_root / "src"
    ) not in sys.path else None

    # We give the user's script the module name "deploy_script"
    spec = importlib.util.spec_from_file_location("deploy_script", script_path)
    if spec is None:
        logger.error(f"Cannot find module spec for '{script_path}'")
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        logger.error(f"Cannot find loader for '{script_path}'")
        sys.exit(1)

    module.__dict__["boa"] = boa
    spec.loader.exec_module(module)

    if hasattr(module, "main") and callable(module.main):
        result = module.main()
        return result
    else:
        logger.info("No main() function found. Executing script as is...")
    sys.path.pop(0)
    sys.path.pop(0)

def get_script_path(script_name_or_path: Path | str) -> Path:
    script_path = Path(script_name_or_path)
    root = get_config().get_root()

    if script_path.suffix != ".py":
        script_path = script_path.with_suffix(".py")

    if not script_path.is_absolute():
        if root not in script_path.parts:
            script_path = root / "script" / script_path
        else:
            script_path = root / script_path

    if not script_path.exists():
        logger.error(f"{script_path} not found")

    return script_path