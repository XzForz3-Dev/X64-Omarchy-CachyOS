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
   - Tu deber es deducir la ruta relativa de la Bóveda (asume que `X64-AI-Brain-Vault` está clonada en el mismo directorio que este proyecto) y copiar el archivo de memoria local hacia `../X64-AI-Brain-Vault/X64-Omarchy-CachyOS/x64_omarchy_memory.md`.
   - Luego, debes ejecutar comandos de terminal dentro de esa carpeta de la Bóveda (`git add .`, `git commit` y `git push origin main`) para sincronizar silenciosamente el cerebro de la IA en la nube.
</RULE[auto_sync_system]>

<RULE[filosofia_de_pruebas_estricta]>
## Regla de Oro: Flujo de Pruebas "Git Pull y Reinstalar"

Tienes TERMINANTEMENTE PROHIBIDO sugerirle al usuario "comandos manuales rápidos" (como usar pacman directamente en la terminal, rm, sed, etc.) para saltarse un bug del instalador.
El objetivo del proyecto es tener un instalador automatizado a prueba de balas.
Por lo tanto, la ÚNICA VÍA válida para probar un arreglo es:
1. El agente modifica el script `x64-install.py` o `x64-install.sh`.
2. El agente hace `git push`.
3. El usuario entra a la TTY, hace `git pull` y REINSTALA el sistema entero.

Si el instalador falla, se arregla el instalador. NUNCA se arregla el sistema en vivo parcheando por detrás.
</RULE[filosofia_de_pruebas_estricta]>
