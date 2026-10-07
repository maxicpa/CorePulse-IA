from pathlib import Path

from corepulse_ai.runtime_config import ensure_shared_env, load_shared_env, read_env_file


def test_shared_env_is_created_outside_project(tmp_path, monkeypatch):
    shared = tmp_path / 'CorePulse' / 'corepulse_ai.env'
    monkeypatch.setenv('COREPULSE_AI_ENV_FILE', str(shared))
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    project = tmp_path / 'CorePulse_V100'
    project.mkdir()
    (project / '.env.example').write_text('GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    status = ensure_shared_env(project, migrate_legacy=False)
    assert Path(status['path']) == shared
    assert shared.is_file()
    assert not status['groq_ready']


def test_shared_env_migrates_previous_version_without_printing_secret(tmp_path, monkeypatch):
    shared = tmp_path / 'persistent' / 'corepulse_ai.env'
    monkeypatch.setenv('COREPULSE_AI_ENV_FILE', str(shared))
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    current = tmp_path / 'CorePulse_V100'
    previous = tmp_path / 'CorePulse_V099'
    current.mkdir(); previous.mkdir()
    (current / '.env.example').write_text('GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    (previous / '.env').write_text('GROQ_API_KEY=test-secret-value\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    status = ensure_shared_env(current)
    values = read_env_file(shared)
    assert status['migrated'] is True
    assert status['groq_ready'] is True
    assert values['GROQ_API_KEY'] == 'test-secret-value'


def test_blank_existing_shared_env_can_migrate_later(tmp_path, monkeypatch):
    shared = tmp_path / 'persistent' / 'corepulse_ai.env'
    shared.parent.mkdir(parents=True)
    shared.write_text('GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    monkeypatch.setenv('COREPULSE_AI_ENV_FILE', str(shared))
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    current = tmp_path / 'CorePulse_V100'
    previous = tmp_path / 'CorePulse_V098'
    current.mkdir(); previous.mkdir()
    (current / '.env.example').write_text('GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    (previous / '.env').write_text('GROQ_API_KEY=legacy-key\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    status = ensure_shared_env(current)
    assert status['migrated'] is True
    assert read_env_file(shared)['GROQ_API_KEY'] == 'legacy-key'


def test_parent_corepulse_env_is_also_migrated(tmp_path, monkeypatch):
    shared = tmp_path / 'persistent' / 'corepulse_ai.env'
    monkeypatch.setenv('COREPULSE_AI_ENV_FILE', str(shared))
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    container = tmp_path / 'CorePulse'
    current = container / 'CorePulse_V100'
    current.mkdir(parents=True)
    (container / '.env').write_text('GROQ_API_KEY=parent-key\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    (current / '.env.example').write_text('GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    status = ensure_shared_env(current)
    assert status['migrated'] is True
    assert read_env_file(shared)['GROQ_API_KEY'] == 'parent-key'


def test_cli_loader_reuses_shared_config_across_versions(tmp_path, monkeypatch):
    shared = tmp_path / 'CorePulse' / 'corepulse_ai.env'
    shared.parent.mkdir(parents=True)
    shared.write_text('GROQ_API_KEY=persisted-key\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8')
    monkeypatch.setenv('COREPULSE_AI_ENV_FILE', str(shared))
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.delenv('GROQ_MODEL', raising=False)
    status = load_shared_env(tmp_path / 'CorePulse_V999')
    assert status['groq_ready'] is True
    assert status['model'] == 'openai/gpt-oss-120b'


def test_explicit_env_file_is_isolated_from_windows_credential_manager(tmp_path, monkeypatch):
    """Una prueba/ejecución portable no debe leer ni modificar credenciales reales del usuario."""
    from core import ai_credentials

    shared = tmp_path / 'isolated' / 'corepulse_ai.env'
    monkeypatch.setenv('COREPULSE_AI_ENV_FILE', str(shared))
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    monkeypatch.setattr(ai_credentials, 'read_secret', lambda _name: 'real-user-secret')

    def _must_not_save(_name, _secret):
        raise AssertionError('No se debe tocar Windows Credential Manager con COREPULSE_AI_ENV_FILE explícito')

    monkeypatch.setattr(ai_credentials, 'save_secret', _must_not_save)

    project = tmp_path / 'CorePulse_V100'
    previous = tmp_path / 'CorePulse_V099'
    project.mkdir(); previous.mkdir()
    (project / '.env.example').write_text(
        'GROQ_API_KEY=\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8'
    )
    (previous / '.env').write_text(
        'GROQ_API_KEY=test-isolated-key\nGROQ_MODEL=openai/gpt-oss-120b\n', encoding='utf-8'
    )

    status = ensure_shared_env(project)
    assert status['migrated'] is True
    assert status['credential_ready'] is False
    assert status['groq_ready'] is True
    assert read_env_file(shared)['GROQ_API_KEY'] == 'test-isolated-key'
