# CorePulse-IA · ISY0101

Módulo académico de **CorePulse AI** para la Evaluación Parcial 1 de **ISY0101 · Ingeniería de Soluciones con IA**.

**Integrantes:** Tomás Hoyt y Maximiliano Carrasco · Ingeniería en Informática · Duoc UC, sede Valparaíso.

## Alcance

CorePulse ya existía como aplicación de monitoreo. Este repositorio separa únicamente el trabajo evaluado en el ramo: **LLM + RAG + prompting + routing + control de contexto + validación + trazabilidad + pruebas**. La telemetría verificada es la fuente de verdad; si un dato no existe, se conserva como `N/A` (`REAL_OR_NA`).

## Flujo

`consulta + telemetría → sanitización → routing → RAG → Prompt Contract 3.2 → LLM → controles duros Python → validator → evidencia`

El LLM interpreta; **no decide sensores, no reemplaza valores medidos y no inventa datos ausentes**.

## Requisitos

- Windows 10/11 para la integración con CorePulse.
- Python 3.12.
- Para pruebas locales: `pytest`.
- Para demo real: cuenta/API key de Groq.

## Instalación

```powershell
py -3.12 -m pip install -r requirements.txt
```

No subir credenciales. `.env` está ignorado por Git.

## Prueba rápida sin API

```powershell
py -3.12 tools\corepulse_ai_cli.py --provider mock --query "Analiza el uso y la temperatura de CPU." --telemetry examples\corepulse_ai\telemetry_cpu_hot.json
```

## Pruebas automáticas

```powershell
py -3.12 -m pytest -q
py -3.12 tools\isy0101_self_check.py
```

También están disponibles `scripts\01_preparar_entorno.bat` y `scripts\02_pruebas.bat`.

## Demo real con Groq

La demo real es opcional. Para ejecutarla se necesita una cuenta de Groq y una API key propia. **No compartir ni subir la clave al repositorio.**

En PowerShell puede configurarse solo para la sesión actual:

```powershell
$env:GROQ_API_KEY="TU_API_KEY"
```

### Caso 1 · Temperatura disponible

Este caso usa el ejemplo reproducible con CPU `96 %`, temperatura `94 °C` y RAM `72 %`:

```powershell
py -3.12 tools\corepulse_ai_cli.py --provider groq --query "Analiza el uso y la temperatura de CPU porque el PC esta funcionando lento." --telemetry examples\corepulse_ai\telemetry_cpu_hot.json
```

El resultado esperado debe incluir:

```text
provider.name = groq
provider.real_llm = true
validation.valid = true
```

### Caso 2 · REAL_OR_NA

Este caso usa intencionalmente una temperatura `N/A` para demostrar que CorePulse-IA **no inventa una medición ausente**:

```powershell
py -3.12 tools\corepulse_ai_cli.py --provider groq --query "Analiza la CPU. Si no existe temperatura real, no la inventes." --telemetry examples\corepulse_ai\telemetry_cpu_na.json
```

El resultado esperado debe conservar:

```text
cpu_temperature = N/A
validation.valid = true
```

Al terminar la prueba, la variable temporal puede eliminarse con:

```powershell
Remove-Item Env:GROQ_API_KEY
```

Las evidencias reales ya incluidas en el repositorio están en `evidence/demo_llm_real.json` y `evidence/demo_llm_real_na.json`. La evidencia nueva solo se guarda si el proveedor es real y `validation.valid = true`.

## Casos reproducibles

`examples/corepulse_ai/` incluye CPU real/N/A y casos de GPU, memoria, almacenamiento, red, sistema y consulta general. `tests/corepulse_ai/test_route_coverage.py` comprueba las siete rutas.

## Evidencias incluidas

- `evidence/demo_llm_real.json`: Groq real, CPU 96 %, 94 °C, RAM 72 %, validación exitosa.
- `evidence/demo_llm_real_na.json`: Groq real, temperatura `N/A`, validación exitosa.
- `evidence/dry_run/`: salidas deterministas de todas las rutas.
- `evidence/pruebas/`: resultados de pytest y self-check de esta entrega.

## Estructura

```text
core/corepulse_ai/       pipeline, prompts, RAG, routing, providers, validator
knowledge/corepulse_ai/  corpus interno y externo controlado
examples/corepulse_ai/   telemetría reproducible
tests/corepulse_ai/      pruebas específicas del módulo
tools/                   CLI y self-check
scripts/                 comandos Windows de apoyo
docs/                    arquitectura, RAG, prompts, bocetos y trazabilidad
evidence/                evidencia real y determinista
```

## Documentación clave

- `docs/arquitectura/corepulse_ai.md`
- `docs/corepulse_ai/pipeline_rag.md`
- `docs/corepulse_ai/prompt_engineering.md`
- `docs/corepulse_ai/pruebas_y_evidencias.md`
- `docs/corepulse_ai/operacion.md`
- `docs/corepulse_ai/matriz_pauta_codigo.md`
- `docs/corepulse_ai/entrega_checklist.md`


## Seguridad y limitaciones

- No hay navegación web autónoma en cada consulta; las fuentes externas están curadas.
- El retriever es lexical/determinista, no vectorial.
- Las acciones sensibles del sistema no son ejecutadas por el módulo académico.
- Una salida de LLM puede ser incorrecta; por eso existe un validator determinista y un máximo de un intento de corrección controlada para proveedores reales.
- `--live` requiere que el módulo esté integrado dentro del proyecto CorePulse completo; el repositorio académico funciona de forma independiente con los JSON de ejemplo.


## Integración continua

`.github/workflows/tests.yml` ejecuta pytest y el self-check en Windows/Python 3.12 cada vez que se hace push o pull request.
