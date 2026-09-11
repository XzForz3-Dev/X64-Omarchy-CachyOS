<div align="center">
  <pre>
██╗  ██╗ ██████╗ ██╗  ██╗
╚██╗██╔╝██╔════╝ ██║  ██║
 ╚███╔╝ ███████╗ ███████║
 ██╔██╗ ██╔═══██╗╚════██║
██╔╝ ██╗╚██████╔╝     ██║
╚═╝  ╚═╝ ╚═════╝      ╚═╝
   [ X64 STUDIOS ]
  </pre>
  <h1>X64-Omarchy-CachyOS Installer</h1>
  <p><b>El instalador TUI definitivo y cyberpunk para desplegar Omarchy sobre CachyOS.</b></p>
  <p><b>El instalador interactivo definitivo para desplegar el ecosistema Omarchy sobre la potencia bruta de CachyOS.</b></p>
  
  [![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://python.org)
  [![CachyOS](https://img.shields.io/badge/OS-CachyOS-008080.svg)](https://cachyos.org/)
  [![Architecture](https://img.shields.io/badge/Arch-Hybrid%20Sync-purple.svg)]()
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

## ⚡ ¿Qué es esto?
## ⚡ Filosofía del Proyecto

Este repositorio contiene la versión **Mega Dashboard (Python TUI Edition)** del instalador de Omarchy, optimizado exclusivamente para **CachyOS**. 
Este repositorio aloja la **X64 Mega Dashboard Edition** de Omarchy. 

Hemos transformado el antiguo y rígido script de bash en una **interfaz gráfica de terminal (TUI) 2D interactiva**, escrita íntegramente en Python (con la potencia gráfica de la librería `rich`). Esto permite seleccionar entornos de escritorio, navegadores, drivers y herramientas de productividad utilizando simplemente el teclado, con un aspecto visual impresionante.
Nos alejamos de los rígidos y peligrosos scripts en bash tradicionales para construir un verdadero **Motor de Instalación Interactivo en Python**. El objetivo de este proyecto es ambicioso: fusionar la asombrosa estética visual y utilidades exclusivas de **Omarchy (Basecamp)** con la extrema optimización y rendimiento en hardware (AVX2, BORE, BTRFS) nativo de **CachyOS**, todo protegido por una arquitectura de ejecución en tiempo real que aísla entornos y previene fallos del sistema anfitrión.

## 🚀 Características Principales
*(Placeholder: 📸 Inserta aquí un GIF de 10 segundos mostrando la TUI de instalación en acción)*

*   **TUI 2D en Python:** Navegación fluida por teclado. Di adiós a escribir respuestas 'S/N' en scripts aburridos.
*   **Security Gateway:** Un sistema de autenticación de seguridad en la terminal (estilo Matrix) que protege la ejecución del instalador.
*   **Gestión Inteligente de Errores:** Intercepta bloqueos de `pacman`, paquetes rotos o caídas de red, dándote la opción interactiva de *Reintentar, Ignorar o Abortar* sin romper la instalación.
*   **Optimización Extrema (Multicore):** Uso de compresión `zstd -T0` para initramfs, reemplazo de llamadas del sistema (cp) por librerías nativas de Python y filtrado de espejos para acelerar el despliegue al máximo.
*   **Arquitectura Híbrida (Lo mejor de ambos mundos):** El sistema inyecta nativamente los repositorios oficiales de Omarchy (`pkgs.omarchy.org`) para mantener actualizadas las aplicaciones exclusivas (Tensaku, Omarchy-nvim, etc.) directamente desde el creador, mientras los scripts críticos del sistema son controlados y protegidos por nuestro repositorio.
*   **Auto-Mantenimiento (CI/CD Shield con Fusión Estricta):** Integración nativa con GitHub Actions (Robot Híbrido) para rastrear y fusionar automáticamente actualizaciones de código oficiales del proyecto base (Upstream). El robot opera bajo una política de "Fusión Estricta", deteniendo la integración de manera segura y solicitando intervención manual (Adaptación) si detecta que el creador modificó líneas estructurales que nosotros adaptamos para CachyOS, evitando así la pérdida silenciosa de código.
*   **Perfiles de Entorno Exclusivos:** Soporte de primera clase para **Hyprland** (con estética Tokyo Night) y **Cinnamon (X64 Edition)** hibridado con la terminal acelerada por hardware **Kitty**, además de estar pre-armado para Gaming (Steam, Proton, MangoHud).
*   **Optimizado para CachyOS:** Aprovecha la arquitectura BTRFS+Snapper de CachyOS y sus repositorios optimizados (v3/AVX2).
*   **Aceleración de Video (VA-API):** Inyección automática de drivers y banderas (flags) en navegadores para reproducir video usando la tarjeta gráfica, ahorrando batería y CPU.
*   **Animación de Arranque (Plymouth):** Inyección nativa a nivel de Kernel (mkinitcpio) y gestor de arranque (Limine/GRUB) para un inicio 100% gráfico.
## 🚀 Arsenal de Ingeniería: Características Clave

### 1. 🖥️ Mega Dashboard Interactivo (TUI 2D)
* **Navegación Visual:** Construido sobre la librería `rich` de Python, ofrece una interfaz TUI navegable por teclado.
* **Control Inteligente de Errores:** Intercepta bases de datos bloqueadas (`pacman.lck`), caídas de red o errores de disco fd 7, ofreciendo recuperación interactiva al usuario (`Reintentar, Ignorar, Abortar`).
* **Cloud-Native:** No necesitas descargar ISOs personalizadas. Cargas un Live USB limpio de CachyOS, ejecutas el clon y el instalador muta el sistema base en vivo.

### 2. 🛡️ Sincronización Híbrida 100% Pura (CI/CD Shield)
Mantenemos una rama sincronizada robóticamente con el código original de Basecamp, asegurando que recibas siempre las últimas herramientas (`ttfx`, `tensaku`, `omacalc`, `quickshell`).
* **Filtro Negro (Blacklist) en Python:** El motor lee las actualizaciones oficiales, pero **destruye dinámicamente en memoria** dependencias peligrosas enviadas por upstream (kernels genéricos de Ubuntu/Arch, gestores de arranque forzados o drivers incompatibles) antes de compilar, protegiendo los kernels ultra-optimizados de CachyOS.
* **Jerarquía de Repositorios:** Inyecta repositorios de forma inteligente en `pacman.conf` para ganar prioridad y resolver automáticamente conflictos de dependencias (ej. `quickshell` vs `noctalia-qs`).

### 3. 🧠 Arquitectura de Chasis Puro (Aislamiento de Entornos)
El instalador actúa como un enrutador de perfiles estrictos:
* Si seleccionas **KDE Plasma, Cinnamon o Niri**, el sistema respeta el "Chasis Puro" de CachyOS, inyectando los temas nativos desde `/etc/skel/` sin contaminar tu disco con dependencias huérfanas de Wayland.
* Si seleccionas **Hyprland (Omarchy Oficial)**, se despliega el ecosistema visual completo.

### 4. 🎮 Enrutamiento Inteligente de Gestores de Sesión (SDDM vs TTY)
X64 Studios diseñó una lógica de hardware a prueba de fallos para GPUs modernas y *legacy*:
* **Hardware Moderno:** Recibe un tema SDDM personalizado de Omarchy con estructura de autologin a prueba de errores.
* **Hardware Legacy (ej. NVIDIA GTX antiguas):** El instalador detecta tarjetas inestables con Wayland y evita que tu pantalla se quede en negro desactivando SDDM. En su lugar, despliega un **Dashboard Interactivo en TTY1** bajo consola `fish`, permitiéndote lanzar Hyprland de forma segura manual.

### 5. ⚙️ Optimizaciones de Sistema y QoL (Quality of Life)
* **Security Gateway:** Animación de autenticación de seguridad en la terminal (estilo Cyberpunk) que gestiona privilegios `sudo` y limpia cachés (Core Override).
* **Actualizador Inteligente (Auto-Stash):** El botón de actualización gráfica (`omarchy update`) soporta git pull con `--autostash`. Esto significa que si modificas tu barra superior a tu gusto, el actualizador no crasheará; guardará tus cambios, actualizará el núcleo, y restaurará tu personalización de fondo.
* **Aceleración VA-API:** Inyección automática de flags en navegadores (Chromium/Firefox) para procesar video en la GPU y ahorrar batería.
* **Soporte HiDPI Automático:** Inyección al vuelo de `scale = "auto"` en Hyprland para monitores 2K/4K.
* **Plymouth Nativo:** Animación de arranque 100% gráfica inyectada en `mkinitcpio`, soportando tanto Limine como GRUB.

## 🛠️ Requisitos Previos

1.  Estar corriendo un Live USB de **CachyOS** (o tener una instalación base de Arch/CachyOS funcional).
2.  Tener conexión a Internet activa.
3.  Tener el administrador de paquetes `pacman` configurado.
4.  No ejecutar el script como usuario `root`. El instalador pedirá `sudo` cuando sea estrictamente necesario.
1. Estar corriendo un Live USB de **CachyOS** (o tener una instalación base de consola funcional).
2. Conexión a Internet activa y repositorios sincronizados.
3. No ejecutar el script como usuario `root`. El Security Gateway gestionará los permisos.

## 📥 Instrucciones de Instalación

Para invocar el menú interactivo y comenzar la *metamorfosis* de tu sistema, simplemente clona este repositorio y ejecuta el lanzador:
Inicia la metamorfosis de tu sistema con un solo bloque de código:

```bash
# 1. Clonar el repositorio
git clone https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git
git clone -b quattro https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git

# 2. Entrar al directorio
cd X64-Omarchy-CachyOS

# 3. Dar permisos de ejecución al lanzador
# 3. Dar permisos de ejecución
chmod +x x64-install.sh

# 4. Iniciar la magia (No uses sudo aquí)
# 4. Iniciar el Gateway (No uses sudo aquí)
./x64-install.sh
```

El script `x64-install.sh` se encargará automáticamente de descargar las dependencias visuales necesarias (como `python-rich` y `fastfetch`) antes de invocar la interfaz principal 100% nativa en Python.
*(El lanzador auto-instalará las dependencias visuales de Python y `fastfetch` antes de invocar el Mega Dashboard).*

## 📂 Estructura del Repositorio

*   `x64-install.sh`: El lanzador y gestor de dependencias inicial.
*   `security_gateway.py`: La pantalla de acceso (Login) que protege el inicio del programa.
*   `x64-install.py`: El "cerebro" del instalador. Dibuja la TUI de selección de paquetes y ejecuta el flujo de instalación.
*   `install/`: Contiene las listas de paquetes principales y extendidos (`.packages`) que la interfaz lee en vivo.
*   `config/` & `themes/`: Dotfiles y archivos de configuración que se inyectan en el sistema destino (Waybar, Hyprland, etc).

## 🧑‍💻 Créditos y Autoría

*   **Desarrollo del Instalador (Python TUI Edition):** [X64 Studios]
*   **Estructura Base / Inspiración Original:** [Omarchy by DHH](https://omarchy.org).
* **Arquitectura, Mega Dashboard y Adaptación CachyOS:** [X64 Studios]
* **Código Base y Ecosistema Original:** [Omarchy by DHH](https://omarchy.org).

---
<div align="center">
  <i>"Wake up, Neo... The Matrix has you."</i>
</div>
