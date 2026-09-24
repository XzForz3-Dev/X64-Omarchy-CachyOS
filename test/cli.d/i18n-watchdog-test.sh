#!/bin/bash
# Test para verificar que ninguna traducción haya quedado huérfana tras actualizar upstream.

echo "Ejecutando el Perro Guardián de Traducciones (i18n Watchdog)..."

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DICT_FILE="$ROOT_DIR/lang/es_ES.json"
SOURCE_DIR="$ROOT_DIR/shell"

if [[ ! -f "$DICT_FILE" ]]; then
    echo ">> [SKIP] No se encontró $DICT_FILE. Saltando prueba de Watchdog."
    exit 0
fi

# Extraer llaves en inglés usando python3
KEYS=$(python3 -c "import json, sys; d=json.load(open(sys.argv[1])); print('\n'.join(d.keys()))" "$DICT_FILE")
ORPHAN_COUNT=0

while IFS= read -r ENG_STRING; do
    [[ -z "$ENG_STRING" ]] && continue
    
    if ! grep -qF "\"$ENG_STRING\"" -R "$SOURCE_DIR" "$ROOT_DIR/bin"; then
        echo "[ERROR] Traducción huérfana: El texto original \"$ENG_STRING\" ya no existe en el código (shell/ o bin/)."
        ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
    fi
done <<< "$KEYS"

if (( ORPHAN_COUNT > 0 )); then
    echo ">> [FALLO] El Watchdog detectó $ORPHAN_COUNT textos en inglés que desaparecieron o cambiaron."
    echo ">> Por favor, actualiza lang/es_ES.json."
    exit 1
else
    echo ">> [ÉXITO] Todas las traducciones de es_ES.json están vigentes. ¡Watchdog OK!"
    exit 0
fi
