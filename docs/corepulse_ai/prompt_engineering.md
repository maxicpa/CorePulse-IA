# Prompt Contract 3.2

Este documento describe el comportamiento implementado. La fundamentación académica y las conclusiones del equipo deben ser redactadas por los integrantes de acuerdo con las reglas de la evaluación.

## Separación de contextos

El prompt usa bloques explícitos:

- `USER_QUERY_UNTRUSTED`
- `CONVERSATION_HISTORY_UNTRUSTED`
- `VERIFIED_TELEMETRY`
- `VERIFIED_HARDWARE_CONTEXT`
- `RAG_SOURCES`
- `OUTPUT_CONTRACT`

La jerarquía declarada en el prompt coloca `VERIFIED_TELEMETRY` como única fuente de verdad para valores medidos. El historial y la consulta sirven como contexto, pero no pueden crear o modificar sensores.

## REAL_OR_NA

El contrato indica que una métrica ausente debe permanecer `N/A`. Además del prompt, el pipeline sustituye siempre `response.measured_data` por el diccionario producido por la capa determinista de normalización.

El validador agrega guardas deterministas para detectar en `interpretation` algunas contradicciones verificables, por ejemplo afirmar una temperatura concreta o un estado térmico para CPU/GPU cuando esa métrica está `N/A`.

## Trazabilidad RAG

`retrieved_information` y `recommendations` deben ser listas de textos con referencias `[S#]`. El validador comprueba que las referencias existan en las fuentes recuperadas. El pipeline sustituye `response.sources` por el manifiesto real de la recuperación.

## Causalidad e incertidumbre

El contrato solicita separar observación de causalidad. Si las métricas y los fragmentos recuperados no permiten confirmar una causa raíz, la salida debe declarar incertidumbre en vez de presentar una hipótesis como hecho.

## Seguridad

El prompt permite recomendaciones, pero no autoriza afirmar que se ejecutaron cambios sensibles. La capa académica no contiene ejecución automática de ajustes del sistema.

## Temperatura del modelo

Los proveedores de demo usan temperatura baja para reducir variabilidad. Esta configuración no constituye la protección principal: la telemetría, las fuentes y la validación se controlan fuera del LLM.
