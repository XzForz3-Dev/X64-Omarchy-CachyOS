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
  <p><b>El instalador interactivo definitivo para desplegar el ecosistema Omarchy sobre la potencia bruta de CachyOS.</b></p>
  
  [![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://python.org)
  [![CachyOS](https://img.shields.io/badge/OS-CachyOS-008080.svg)](https://cachyos.org/)
  [![Architecture](https://img.shields.io/badge/Arch-Hybrid%20Sync-purple.svg)]()
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

## ⚡ Filosofía del Proyecto

Este repositorio aloja la **X64 Mega Dashboard Edition** de Omarchy. 

Nos alejamos de los rígidos y peligrosos scripts en bash tradicionales para construir un verdadero **Motor de Instalación Interactivo en Python**. El objetivo de este proyecto es ambicioso: fusionar la asombrosa estética visual y utilidades exclusivas de **Omarchy (Basecamp)** con la extrema optimización y rendimiento en hardware (AVX2, BORE, BTRFS) nativo de **CachyOS**, todo protegido por una arquitectura de ejecución en tiempo real que aísla entornos y previene fallos del sistema anfitrión.

*(Placeholder: 📸 Inserta aquí un GIF de 10 segundos mostrando la TUI de instalación en acción)*

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

1. Estar corriendo un Live USB de **CachyOS** (o tener una instalación base de consola funcional).
2. Conexión a Internet activa y repositorios sincronizados.
3. No ejecutar el script como usuario `root`. El Security Gateway gestionará los permisos.

## 📥 Instrucciones de Instalación

Inicia la metamorfosis de tu sistema con un solo bloque de código:

```bash
# 1. Clonar el repositorio
git clone -b quattro https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git

# 2. Entrar al directorio
cd X64-Omarchy-CachyOS

# 3. Dar permisos de ejecución
chmod +x x64-install.sh

# 4. Iniciar el Gateway (No uses sudo aquí)
./x64-install.sh
```

*(El lanzador auto-instalará las dependencias visuales de Python y `fastfetch` antes de invocar el Mega Dashboard).*

## 🧑‍💻 Créditos y Autoría

* **Arquitectura, Mega Dashboard y Adaptación CachyOS:** [X64 Studios]
* **Código Base y Ecosistema Original:** [Omarchy by DHH](https://omarchy.org).

---
<div align="center">
  <i>"Wake up, Neo... The Matrix has you."</i>
</div>
