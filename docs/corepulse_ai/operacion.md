# Guía de operación

## 1. Preparar entorno

Desde la raíz del repositorio:

```powershell
py -3.12 -m pip install -r requirements.txt
```

O ejecutar `scripts\01_preparar_entorno.bat`.

## 2. Validar la entrega sin API

```powershell
py -3.12 -m pytest -q
py -3.12 tools\isy0101_self_check.py
```

Resultado esperado en esta entrega: **32 pruebas aprobadas** y `RESULTADO: PASS`. El registro está en `evidence/pruebas/`.

## 3. Demo determinista

```powershell
scripts\03_demo_mock.bat
```

Sirve para explicar routing, RAG, trazabilidad y `REAL_OR_NA` sin depender de Internet.

## 4. Demo real

Configurar `GROQ_API_KEY` localmente y ejecutar `scripts\04_demo_groq_cpu.bat` o `scripts\05_demo_groq_na.bat`.

Nunca copiar la API key al repositorio ni a una captura pública.

## 5. Qué revisar en la salida

- `route` coincide con la consulta.
- `measured_data` conserva exactamente las métricas de entrada.
- máximo cuatro elementos en `retrieved_sources`.
- `retrieval_trace` explica la selección.
- `provider.real_llm` distingue demo real de mock.
- `validation.valid` debe ser `true` para evidencia final.
