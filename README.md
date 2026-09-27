<div align="center">
  <img src="https://raw.githubusercontent.com/XzForz3-Dev/X64-Omarchy-CachyOS/quattro/logo.txt" alt="X64 LIOS Logo" width="100%">
  
  # X64 LIOS 
  *El sistema operativo de próxima generación para Gaming, Ciberseguridad y Desarrollo.*
  
  [![Base: CachyOS](https://img.shields.io/badge/Base-CachyOS-00a86b?style=for-the-badge&logo=archlinux)](https://cachyos.org/)
  [![Compositor: Hyprland](https://img.shields.io/badge/Compositor-Hyprland-00a86b?style=for-the-badge&logo=hyprland)](https://hyprland.org/)
  [![Licencia: MIT](https://img.shields.io/badge/Licencia-MIT-blue?style=for-the-badge)](LICENSE)
  [![Versión](https://img.shields.io/badge/Versi%C3%B3n-2.0.0--Stable-purple?style=for-the-badge)]()
  [![Good First Issues](https://img.shields.io/github/issues/XzForz3-Dev/X64-Omarchy-CachyOS/good%20first%20issue?style=for-the-badge&color=green)](https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS/issues)
</div>

<br>

**X64 LIOS** es un fork altamente optimizado y rediseñado de [Omarchy](https://omarchy.org), construido sobre la sólida y veloz base de **CachyOS**. Está diseñado desde cero para usuarios exigentes que buscan el máximo rendimiento en videojuegos, un entorno de desarrollo seguro, y una estética *Cyberpunk* inigualable.

---

## ⚡ Características Principales

* 🎮 **Gaming Extremo:** Aprovecha los kernels personalizados BORE de CachyOS y optimizaciones LTO para los máximos FPS.
* 🛡️ **Zero-Amnesia IA:** Arquitectura interna preparada para asistentes de Inteligencia Artificial que sincronizan memoria y despliegues sin interrupciones.
* 🖥️ **Terminal Premium (Overhaul):**
  * Emulador `foot` hiper-rápido impulsado por Wayland.
  * Prompt multilínea enriquecido con [Starship](https://starship.rs/).
  * Árbol visual de hardware nativo impulsado por `fastfetch` con colores de acento neón.
* 🎨 **Interfaz de Usuario (Quickshell):** Un escritorio QML moderno, minimalista y ultra reactivo sin la pesadez de los entornos tradicionales.
* 🔄 **Actualizador Atómico (TUI/GUI):** Sistema de actualización a prueba de balas inspirado en arquitecturas inmutables, con recuperación instantánea.

## 📸 Galería

> **Nota para colaboradores:** *¡Sube aquí las capturas de tu escritorio! [Agrega una PR con tus capturas de Hyprland y la Terminal]*
*(Espacio reservado para capturas de pantalla de la terminal transparente, el menú de aplicaciones y Fastfetch)*

## 🚀 Instalación

> **Advertencia:** X64 LIOS es un sistema operativo completo. Se recomienda instalarlo en una Máquina Virtual (QEMU/KVM) o en hardware dedicado.

1. Instala una base limpia de **CachyOS**.
2. Abre la terminal (`Ctrl + Alt + T` / `Ctrl + Alt + F3`).
3. Clona este repositorio e inicia el proceso de inyección atómica:

```bash
git clone https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git
cd X64-Omarchy-CachyOS
python3 x64-install.py
```

4. Sigue las instrucciones interactivas del asistente (TUI) y reinicia el sistema.

## 🤝 ¿Cómo Colaborar?

¡La comunidad de X64 Studios te necesita! Si eres un apasionado de Linux, Wayland, Bash o QML, hay un lugar para ti.

1. Revisa la pestaña de **[Issues](https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS/issues)** y busca las etiquetas `good first issue` o `help wanted`.
2. **Haz un Fork** del repositorio.
3. Lee nuestro manifiesto interno de desarrollo en `.agents/AGENTS.md` para entender nuestras reglas de despliegue.
4. Sube tus mejoras a la rama `quattro` y abre un Pull Request.

**Regla de Oro del Proyecto:** Nunca arreglamos sistemas "en vivo". Si encuentras un bug, parcha el código fuente, sube el PR, y probamos el arreglo reinstalando. *Zero hot-patching.*

## 📜 Créditos

Este proyecto no sería posible sin el trabajo increíble de:
- El equipo de **[CachyOS](https://cachyos.org/)** por el mejor rendimiento de kernel del planeta.
- Los ingenieros de **[37signals (Basecamp)](https://github.com/basecamp/omarchy)** por la robusta arquitectura original de Omarchy.
- **X64 Studios** y la iniciativa Antigravity por la automatización e integración IA.
