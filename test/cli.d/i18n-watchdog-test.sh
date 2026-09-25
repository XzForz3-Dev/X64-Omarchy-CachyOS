#!/bin/bash
# Test para verificar que ninguna traducción haya quedado huérfana tras actualizar upstream.

echo "Ejecutando el Perro Guardián de Traducciones (i18n Watchdog)..."
DICT_FILE="lang/es_ES.json"
SOURCE_DIR="shell"

# Fallback si se ejecuta desde otro lado
if [[ ! -f "$DICT_FILE" ]]; then
    DICT_FILE="../lang/es_ES.json"
    SOURCE_DIR="../shell"
fi
if [[ ! -f "$DICT_FILE" ]]; then
    DICT_FILE="../../lang/es_ES.json"
    SOURCE_DIR="../../shell"
fi

if [[ ! -f "$DICT_FILE" ]]; then
    echo "[SKIP] Diccionario no encontrado, saltando watchdog."
    exit 0
fi

if ! command -v jq &>/dev/null; then
    echo "[SKIP] jq no instalado, saltando watchdog."
    exit 0
fi

KEYS=$(jq -r 'keys[]' "$DICT_FILE")
ORPHAN_COUNT=0

while IFS= read -r ENG_STRING; do
    # Omitimos las traducciones de Omarchy Installer que no están en shell
    if [[ "$ENG_STRING" == "Settings" || "$ENG_STRING" == "Apps" || "$ENG_STRING" == "Learn" || "$ENG_STRING" == "Trigger" || "$ENG_STRING" == "Style" || "$ENG_STRING" == "Setup" || "$ENG_STRING" == "Language" || "$ENG_STRING" == "English" || "$ENG_STRING" == "Español" || "$ENG_STRING" == "Install" || "$ENG_STRING" == "Remove" || "$ENG_STRING" == "Update" || "$ENG_STRING" == "About" || "$ENG_STRING" == "System" || "$ENG_STRING" == "Plugins" || "$ENG_STRING" == "Security" || "$ENG_STRING" == "Config" || "$ENG_STRING" == "Reset Computer" ]]; then
        continue
    fi
    
    # Buscar el texto exacto (con comillas) en la carpeta shell
    if ! grep -qF "\"$ENG_STRING\"" -R "$SOURCE_DIR"; then
        echo "[ERROR] Traducción huérfana: El texto original \"$ENG_STRING\" ya no existe en el código."
        ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
    fi
done <<< "$KEYS"

if (( ORPHAN_COUNT > 0 )); then
    echo ">> El Watchdog detectó $ORPHAN_COUNT textos en inglés que desaparecieron o cambiaron."
    echo ">> Por favor, actualiza $DICT_FILE."
    exit 1
else
    echo ">> Todas las traducciones testeadas están vigentes. ¡Watchdog OK!"
    exit 0
fi
