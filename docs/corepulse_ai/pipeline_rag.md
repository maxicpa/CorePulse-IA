# Pipeline RAG

## Flujo

1. **Entrada:** consulta, telemetría e historial opcional.
2. **Sanitización:** elimina caracteres de control y bloquea patrones básicos de inyección conocidos.
3. **Routing:** clasifica en `cpu`, `gpu`, `memory`, `storage`, `network`, `system` o `general`.
4. **Normalización:** transforma ausencias en `N/A` sin estimación.
5. **Recuperación:** puntúa documentos internos y externos controlados.
6. **Filtro de coherencia:** una ruta específica compite solo con documentos de esa ruta y políticas `general`.
7. **Selección:** máximo cuatro fragmentos; cuando existe evidencia suficiente, se conserva diversidad interna/externa.
8. **Trazabilidad:** se registra `retrieval_trace` con puntaje, componentes y razón de selección.
9. **Prompt Contract:** separa telemetría verificada, fuentes RAG y contexto no confiable.
10. **Generación:** `LLMProvider` devuelve JSON.
11. **Controles duros:** Python sustituye `measured_data` y `sources` por los valores reales del pipeline.
12. **Validación:** estructura, citas, máximo de fuentes y guardas `N/A`.
13. **Corrección controlada:** con un proveedor real, si la primera salida falla, se permite un único segundo intento usando los errores deterministas del validator. La telemetría y las fuentes siguen impuestas por Python.

## Puntaje del retriever

El prototipo utiliza un ranking lexical explicable:

```text
score = token_overlap
      + route_bonus
      + general_bonus
      + source_type_bonus
      + vendor_bonus
      + model_bonus
```

`retrieval_trace` conserva esos componentes para cada `[S#]`. Esto permite mostrar por qué un fragmento fue seleccionado sin depender de razonamiento oculto del LLM.

## Límites del prototipo

El retriever actual no usa embeddings ni una base vectorial. La colección es pequeña y controlada, por lo que el enfoque lexical permite una recuperación reproducible y auditable. Si el corpus creciera, esta capa podría reemplazarse por un retriever vectorial manteniendo el mismo contrato del pipeline.
