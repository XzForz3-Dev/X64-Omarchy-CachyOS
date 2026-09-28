# X64 Mega Installer (Shell Switcher & Theme Adaptation System)

## Concepto Core
El "Mega Instalador" (o X64 Theme & Environment Store) es una aplicación gráfica de "1-clic" diseñada para ofrecer entornos de escritorio comunitarios ultra-avanzados (como Caelestia, Soramane, Outfoxxed de Quickshell) a los usuarios de X64 LIOS.

A diferencia de instalar los temas directamente de internet (lo cual reemplazaría la shell y rompería funciones vitales del sistema), este instalador utiliza **"Versiones Porteadas" (X64 Layouts)**.

## ¿Cómo funciona el porting?
Cualquier "rice" o tema espectacular de la comunidad se divide en dos componentes al integrarlo a X64 LIOS:
1. **Layout / Estructura (QML):** Extraemos la barra de estado flotante, los widgets de música interactivos y las islas dinámicas del tema original y los envolvemos como un "Bar Plugin" dentro del ecosistema modular de X64.
2. **El "ADN" Estético (Theme Engine):** Capturamos el radio de los bordes (`cornerRadius`), la opacidad, la intensidad del *blur* (Glassmorphism) y los colores exactos (`colors.toml`).

## La Magia del "Camaleón" (Integración)
Al instalar un entorno desde el Mega Instalador, el motor inyecta el "ADN" en todo el sistema operativo.
Esto significa que herramientas nativas críticas como:
- El **Menú Gigante** de aplicaciones (Grid).
- La **Pantalla de Bloqueo** de seguridad.
- El sistema de **Notificaciones OSD**.

Automáticamente heredan la estética exacta del tema de la comunidad (ej. Caelestia). El menú gigante de X64 LIOS se transformará visualmente adoptando el desenfoque de cristal y los colores del tema instalado, fusionando la belleza comunitaria con la potencia de las herramientas exclusivas de X64.

## Flujo de Usuario (UX)
1. **Galería**: El usuario abre el Mega Instalador y navega por tarjetas con capturas de pantalla de los entornos.
2. **Instalación (1-Click)**: El instalador descarga la versión "X64-Ready" del entorno desde nuestro repositorio y la aplica inmediatamente sin reiniciar.
3. **Failsafe**: Se proveerá un botón o atajo de pánico para regresar a la Shell Oficial de X64 en caso de fallos.
