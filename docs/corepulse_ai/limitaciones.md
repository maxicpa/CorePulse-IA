# Limitaciones y decisiones técnicas

- El retriever actual es lexical y auditable; no utiliza embeddings. Para el tamaño del prototipo reduce dependencias y permite explicar por qué se recuperó cada fragmento.
- Las fuentes externas están curadas previamente. No existe navegación web autónoma en tiempo de respuesta.
- El LLM puede redactar una interpretación incorrecta aunque la telemetría esté protegida; por ello se valida estructura y trazabilidad, y se debe revisar la salida en la demo.
- La latencia de red y otros datos que requieran una prueba específica permanecen `N/A` si esa prueba no fue ejecutada.
- `MockProvider` es útil para pruebas de integración, pero no demuestra generación real con LLM.
