from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict

_ENV_LINE = re.compile(r'^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$')
_ALLOWED_KEYS = (
    'COREPULSE_AI_BASE_URL',
    'GROQ_API_KEY',
    'GROQ_MODEL',
    'OLLAMA_BASE_URL',
    'OLLAMA_MODEL',
)
_DEFAULTS = {
    'COREPULSE_AI_BASE_URL': 'http://127.0.0.1:8765',
    'GROQ_API_KEY': '',
    'GROQ_MODEL': 'openai/gpt-oss-120b',
    'OLLAMA_BASE_URL': 'http://localhost:11434',
    'OLLAMA_MODEL': '',
}


def shared_env_path() -> Path:
    """Configuración persistente compartida por todas las versiones de CorePulse."""
    override = str(os.getenv('COREPULSE_AI_ENV_FILE') or '').strip()
    if override:
        return Path(override).expanduser()
    base = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
    if base:
        return Path(base) / 'CorePulse' / 'corepulse_ai.env'
    return Path.home() / '.corepulse' / 'CorePulse' / 'corepulse_ai.env'


def _parse_value(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ''
    if value[:1] in {'"', "'"}:
        quote = value[0]
        if len(value) > 1 and value.endswith(quote):
            return value[1:-1]
        return value[1:]
    return re.split(r'\s+#', value, maxsplit=1)[0].strip()


def read_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    try:
        text = path.read_text(encoding='utf-8-sig')
    except Exception:
        return values
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        match = _ENV_LINE.match(line)
        if not match:
            continue
        key, value = match.group(1), _parse_value(match.group(2))
        if key in _ALLOWED_KEYS:
            values[key] = value
    return values


def _write_shared(values: Dict[str, str]) -> Path:
    path = shared_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = dict(_DEFAULTS)
    for key in _ALLOWED_KEYS:
        if key in values:
            merged[key] = str(values[key])
    lines = [
        '# CorePulse AI · configuración persistente del usuario',
        '# Este archivo vive fuera de las carpetas versionadas y no debe subirse a Git.',
        f"COREPULSE_AI_BASE_URL={merged['COREPULSE_AI_BASE_URL']}",
        '',
        f"GROQ_API_KEY={merged['GROQ_API_KEY']}",
        f"GROQ_MODEL={merged['GROQ_MODEL']}",
        '',
        f"OLLAMA_BASE_URL={merged['OLLAMA_BASE_URL']}",
        f"OLLAMA_MODEL={merged['OLLAMA_MODEL']}",
        '',
    ]
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path


def _legacy_candidates(project_root: Path) -> list[Path]:
    """Busca configuraciones antiguas probables sin hacer una búsqueda amplia del disco."""
    candidates: list[Path] = []

    def add(path: Path) -> None:
        try:
            path = path.resolve()
        except Exception:
            pass
        if path.is_file() and path not in candidates:
            candidates.append(path)

    # 1) Versión actual y raíz contenedora (caso típico de VS Code: CorePulse/.env).
    add(project_root / '.env')
    add(project_root.parent / '.env')

    # 2) Versiones hermanas CorePulse_Vxxx, priorizando la versión numérica más alta.
    parent = project_root.parent
    try:
        siblings = []
        for folder in parent.glob('CorePulse_V*'):
            if not folder.is_dir():
                continue
            try:
                if folder.resolve() == project_root.resolve():
                    continue
            except Exception:
                pass
            match = re.search(r'CorePulse_V(\d+)', folder.name, re.IGNORECASE)
            version = int(match.group(1)) if match else -1
            siblings.append((version, folder))
        for _version, folder in sorted(siblings, key=lambda item: item[0], reverse=True):
            add(folder / '.env')
    except Exception:
        pass

    # 3) Un nivel adicional por si la versión actual está dentro de otra carpeta.
    try:
        grandparent = parent.parent
        add(grandparent / '.env')
        for folder in grandparent.glob('CorePulse*/CorePulse_V*'):
            if folder.is_dir():
                add(folder / '.env')
    except Exception:
        pass

    return candidates


def _legacy_values(project_root: Path) -> tuple[Dict[str, str], str | None]:
    # Si el usuario ya exportó GROQ_API_KEY en Windows/PowerShell, también sirve
    # como origen para inicializar la configuración persistente.
    env_key = str(os.getenv('GROQ_API_KEY') or '').strip()
    if env_key:
        values = dict(_DEFAULTS)
        values['GROQ_API_KEY'] = env_key
        env_model = str(os.getenv('GROQ_MODEL') or '').strip()
        if env_model:
            values['GROQ_MODEL'] = env_model
        return values, 'environment:GROQ_API_KEY'

    for candidate in _legacy_candidates(project_root):
        values = read_env_file(candidate)
        if values.get('GROQ_API_KEY'):
            return values, str(candidate)
    return {}, None


def _credential_manager_enabled() -> bool:
    """Indica si esta ejecución debe consultar Windows Credential Manager.

    Un COREPULSE_AI_ENV_FILE explícito se usa como backend aislado/portable
    (por ejemplo, en pruebas). En ese modo no debemos leer ni escribir una
    credencial real del usuario, porque contaminaría el resultado y podría
    impedir probar correctamente las migraciones de .env.
    """
    return not bool(str(os.getenv('COREPULSE_AI_ENV_FILE') or '').strip())


def _credential_groq_key() -> str:
    if not _credential_manager_enabled():
        return ''
    try:
        from core.ai_credentials import read_secret
        return str(read_secret('groq_api_key') or '').strip()
    except Exception:
        return ''


def store_groq_api_key(secret: str) -> dict:
    """Guarda la clave una sola vez, priorizando Windows Credential Manager.

    Si COREPULSE_AI_ENV_FILE fue definido explícitamente, se respeta ese archivo
    como backend y no se toca el Credential Manager del usuario.
    """
    secret = str(secret or '').strip()
    if not secret:
        return {'saved': False, 'backend': None}
    if _credential_manager_enabled():
        try:
            from core.ai_credentials import save_secret
            if save_secret('groq_api_key', secret):
                # Mantiene el archivo compartido sin la credencial en texto plano.
                current = read_env_file(shared_env_path())
                current['GROQ_API_KEY'] = ''
                _write_shared(current)
                return {'saved': True, 'backend': 'windows_credential_manager'}
        except Exception:
            pass
    # Fallback portable: archivo persistente fuera de las carpetas versionadas.
    current = read_env_file(shared_env_path())
    current['GROQ_API_KEY'] = secret
    _write_shared(current)
    return {'saved': True, 'backend': 'shared_env_file'}


def ensure_shared_env(project_root: Path | None = None, *, migrate_legacy: bool = True) -> dict:
    project_root = (project_root or Path(__file__).resolve().parents[2]).resolve()
    path = shared_env_path()
    created = False
    migrated = False
    migrated_from: str | None = None

    current_values = read_env_file(path) if path.is_file() else {}
    credential_key = _credential_groq_key()

    # Primero intenta recuperar la clave del Credential Manager. Si no existe,
    # todavía puede migrar un .env previo. La clave migrada se guarda de forma
    # persistente y, en Windows, deja de depender de carpetas versionadas.
    if migrate_legacy and not current_values.get('GROQ_API_KEY') and not credential_key:
        legacy, legacy_source = _legacy_values(project_root)
        if legacy.get('GROQ_API_KEY'):
            saved = store_groq_api_key(legacy.get('GROQ_API_KEY', ''))
            if saved.get('saved'):
                migrated = True
                migrated_from = legacy_source
                credential_key = _credential_groq_key()
                current_values = read_env_file(path) if path.is_file() else current_values

    if not path.is_file():
        values = read_env_file(project_root / '.env.example')
        _write_shared(values)
        created = True
        current_values = read_env_file(path)

    values = current_values or read_env_file(path)
    return {
        'path': str(path),
        'created': created,
        'migrated': migrated,
        'migrated_from': migrated_from,
        'groq_ready': bool(values.get('GROQ_API_KEY') or credential_key) and bool(values.get('GROQ_MODEL')),
        'credential_ready': bool(credential_key),
        'model': values.get('GROQ_MODEL') or _DEFAULTS['GROQ_MODEL'],
    }


def load_shared_env(project_root: Path | None = None, *, override: bool = False) -> dict:
    status = ensure_shared_env(project_root)
    path = Path(status['path'])
    values = read_env_file(path)
    for key, value in values.items():
        if override or key not in os.environ:
            os.environ[key] = value
    if not str(os.getenv('GROQ_API_KEY') or '').strip():
        credential_key = _credential_groq_key()
        if credential_key:
            os.environ['GROQ_API_KEY'] = credential_key
            status['credential_ready'] = True
    status['groq_ready'] = bool(str(os.getenv('GROQ_API_KEY') or '').strip()) and bool(
        str(os.getenv('GROQ_MODEL') or '').strip()
    )
    status['model'] = str(os.getenv('GROQ_MODEL') or _DEFAULTS['GROQ_MODEL']).strip()
    return status


__all__ = ['shared_env_path', 'ensure_shared_env', 'load_shared_env', 'read_env_file', 'store_groq_api_key']
