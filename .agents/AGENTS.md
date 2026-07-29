# Reglas de Proyecto: X64-Omarchy-CachyOS

Las siguientes reglas son de carácter OBLIGATORIO para Antigravity y cualquier otro agente de IA que opere en este entorno de trabajo (workspace).

<RULE[auto_sync_system]>
## Sistema de Sincronización Automática (Auto-Sync)

Como asistente IA, tu deber principal es garantizar que la documentación y la memoria del proyecto jamás se desfasen respecto al código fuente. 

**Protocolo de Cierre de Tarea:**
CADA VEZ que completes una tarea que involucre crear una nueva función, modificar el flujo del instalador, o cambiar la arquitectura del proyecto, debes cumplir estrictamente con los siguientes pasos antes de dar la tarea por finalizada:

1. **Integridad de Documentación Pública:** 
   - Revisa si el cambio requiere una mención en el `README.md`. Si es así, actualízalo de inmediato.

2. **Integridad de la Memoria (Contexto IA):**
   - Actualiza el archivo de Memoria en la carpeta de Artefactos (ej: `X64_OMARCHY_MEMORY.md`). 
   - Debes reescribir o añadir la nueva información (nuevos scripts, dependencias, lógicas) para que el contexto histórico de la IA esté siempre 100% al día.

3. **Protocolo Git Push:**
   - Realiza un `git commit` descriptivo de tus cambios y ejecuta `git push origin quattro` (o la rama activa) para asegurar que el código está respaldado en la nube.

4. **Sincronización Automática con la Bóveda de IA (Brain Vault):**
   - Tienes terminantemente prohibido pedirle al usuario que copie o suba el archivo manualmente.
   - Tu deber es copiar automáticamente el archivo de memoria local hacia `C:\Users\XzForz3\.gemini\antigravity-ide\scratch\X64-AI-Brain-Vault\x64_omarchy_memory.md`.
   - Luego, debes ejecutar comandos de terminal dentro de esa carpeta (`git add .`, `git commit` y `git push origin main`) para sincronizar silenciosamente el cerebro de la IA en la nube.
</RULE[auto_sync_system]>
