# Control de contexto conversacional

`core/corepulse_ai/conversation.py` conserva únicamente los últimos seis mensajes con rol `user` o `assistant`. Cada contenido se sanitiza y se limita a 1200 caracteres.

El historial se inyecta en una sección distinta del prompt y está explícitamente marcado como **contexto conversacional**, por lo que no puede ser usado como fuente de sensores. Esta separación reduce contaminación de contexto y hace más auditable la respuesta.
