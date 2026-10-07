# Repositorio académico

Repositorio objetivo: `https://github.com/maxicpa/CorePulse-IA`

Este repositorio contiene únicamente el alcance evaluado en ISY0101: pipeline LLM + RAG, prompts, recuperación, validación, ejemplos, pruebas, evidencias y documentación. El producto CorePulse completo se mantiene separado.

Antes de publicar:

```powershell
git status
git remote -v
python -m pytest -q
python tools\isy0101_self_check.py
```

Nunca subir `.env`, claves API ni credenciales.
