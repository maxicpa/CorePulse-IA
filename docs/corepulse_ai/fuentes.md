# Fuentes RAG controladas

La base se divide en `internal_corepulse.json` y `external_controlled.json`. El LLM no navega libremente en cada consulta: recibe únicamente los fragmentos seleccionados por el retriever.

## Cobertura externa

- CPU AMD: especificaciones Ryzen/Tjmax oficiales de AMD.
- CPU Intel: documentación oficial de Intel sobre Tjunction/Tcase.
- GPU: documentación oficial NVIDIA `nvidia-smi` sobre utilización y temperatura.
- Memoria/sistema: documentación Microsoft sobre análisis de memoria y rendimiento.
- Almacenamiento: `Get-StorageReliabilityCounter` y `Get-PhysicalDisk` de Microsoft.
- Red: comando `ping` de Microsoft para conectividad y tiempos de ida y vuelta.

Las fuentes externas contextualizan una medición; nunca crean una lectura inexistente.
