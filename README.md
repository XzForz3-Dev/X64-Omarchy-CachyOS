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
  
  [![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://python.org)
  [![CachyOS](https://img.shields.io/badge/OS-CachyOS-008080.svg)](https://cachyos.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

## ⚡ ¿Qué es esto?

Este repositorio contiene la versión **Mega Dashboard (Python TUI Edition)** del instalador de Omarchy, optimizado exclusivamente para **CachyOS**. 

Hemos transformado el antiguo y rígido script de bash en una **interfaz gráfica de terminal (TUI) 2D interactiva**, escrita íntegramente en Python (con la potencia gráfica de la librería `rich`). Esto permite seleccionar entornos de escritorio, navegadores, drivers y herramientas de productividad utilizando simplemente el teclado, con un aspecto visual impresionante.

## 🚀 Características Principales

*   **TUI 2D en Python:** Navegación fluida por teclado. Di adiós a escribir respuestas 'S/N' en scripts aburridos.
*   **Security Gateway:** Un sistema de autenticación de seguridad en la terminal (estilo Matrix) que protege la ejecución del instalador.
*   **Gestión Inteligente de Errores:** Intercepta bloqueos de `pacman`, paquetes rotos o caídas de red, dándote la opción interactiva de *Reintentar, Ignorar o Abortar* sin romper la instalación.
*   **Optimización Extrema (Multicore):** Uso de compresión `zstd -T0` para initramfs, reemplazo de llamadas del sistema (cp) por librerías nativas de Python y filtrado de espejos para acelerar el despliegue al máximo.
*   **Arquitectura Híbrida (Lo mejor de ambos mundos):** El sistema inyecta nativamente los repositorios oficiales de Omarchy (`pkgs.omarchy.org`) para mantener actualizadas las aplicaciones exclusivas (Tensaku, Omarchy-nvim, etc.) directamente desde el creador, mientras los scripts críticos del sistema son controlados y protegidos por nuestro repositorio.
*   **Auto-Mantenimiento (CI/CD Shield con Fusión Estricta):** Integración nativa con GitHub Actions (Robot Híbrido) para rastrear y fusionar automáticamente actualizaciones de código oficiales del proyecto base (Upstream). El robot opera bajo una política de "Fusión Estricta", deteniendo la integración de manera segura y solicitando intervención manual (Adaptación) si detecta que el creador modificó líneas estructurales que nosotros adaptamos para CachyOS, evitando así la pérdida silenciosa de código.
*   **Perfiles de Entorno Exclusivos:** Soporte de primera clase para **Hyprland** (con estética Tokyo Night) y otros entornos, además de estar pre-armado para Gaming (Steam, Proton, MangoHud).
*   **Optimizado para CachyOS:** Aprovecha la arquitectura BTRFS+Snapper de CachyOS y sus repositorios optimizados (v3/AVX2).
*   **Aceleración de Video (VA-API):** Inyección automática de drivers y banderas (flags) en navegadores para reproducir video usando la tarjeta gráfica, ahorrando batería y CPU.
*   **Animación de Arranque (Plymouth):** Inyección nativa a nivel de Kernel (mkinitcpio) y gestor de arranque (Limine/GRUB) para un inicio 100% gráfico.

## 🛠️ Requisitos Previos

1.  Estar corriendo un Live USB de **CachyOS** (o tener una instalación base de Arch/CachyOS funcional).
2.  Tener conexión a Internet activa.
3.  Tener el administrador de paquetes `pacman` configurado.
4.  No ejecutar el script como usuario `root`. El instalador pedirá `sudo` cuando sea estrictamente necesario.

## 📥 Instrucciones de Instalación

Para invocar el menú interactivo y comenzar la *metamorfosis* de tu sistema, simplemente clona este repositorio y ejecuta el lanzador:

```bash
# 1. Clonar el repositorio
git clone https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git

# 2. Entrar al directorio
cd X64-Omarchy-CachyOS

# 3. Dar permisos de ejecución al lanzador
chmod +x x64-install.sh

# 4. Iniciar la magia (No uses sudo aquí)
./x64-install.sh
```

El script `x64-install.sh` se encargará automáticamente de descargar las dependencias visuales necesarias (como `python-rich` y `fastfetch`) antes de invocar la interfaz principal 100% nativa en Python.

## 📂 Estructura del Repositorio

*   `x64-install.sh`: El lanzador y gestor de dependencias inicial.
*   `security_gateway.py`: La pantalla de acceso (Login) que protege el inicio del programa.
*   `x64-install.py`: El "cerebro" del instalador. Dibuja la TUI de selección de paquetes y ejecuta el flujo de instalación.
*   `install/`: Contiene las listas de paquetes principales y extendidos (`.packages`) que la interfaz lee en vivo.
*   `config/` & `themes/`: Dotfiles y archivos de configuración que se inyectan en el sistema destino (Waybar, Hyprland, etc).

## 🧑‍💻 Créditos y Autoría

*   **Desarrollo del Instalador (Python TUI Edition):** [X64 Studios]
*   **Estructura Base / Inspiración Original:** [Omarchy by DHH](https://omarchy.org).

---
<div align="center">
  <i>"Wake up, Neo... The Matrix has you."</i>
</div>
