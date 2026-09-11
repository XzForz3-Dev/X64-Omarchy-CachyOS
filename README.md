<div align="center">

# 🌌 X64-Omarchy-CachyOS
### El Entorno de Escritorio Definitivo, Optimizado al Máximo.

[![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)](https://archlinux.org/)
[![CachyOS](https://img.shields.io/badge/CachyOS-008080?style=for-the-badge&logo=arch-linux&logoColor=white)](https://cachyos.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Hyprland](https://img.shields.io/badge/Hyprland-00A9FF?style=for-the-badge&logo=hyprland&logoColor=white)](https://hyprland.org/)

Un proyecto de ingeniería avanzada creado por **X64 Studios**. Fusionamos la velocidad brutal y optimización de **CachyOS** con la elegancia estética y productividad extrema de **Omarchy (Hyprland)**.

</div>

---

## 🚀 ¿Qué hace único a este proyecto?

Este no es un simple script de bash (dotfiles). Hemos construido un **motor de despliegue dinámico en Python** de grado corporativo que asegura que el sistema se instale, se actualice y sobreviva sin intervención manual.

### 1. 🖥️ Mega Dashboard Interactivo (TUI)
Olvídate de los scripts que corren ciegamente en la terminal. Hemos diseñado un panel de control inmersivo en 2D.
- **La Boutique de Software Integrada:** Navega usando las flechas del teclado a través de 24 categorías de software exhaustivamente curadas (desde Entornos de Escritorio, Gaming con Proton, Edición 3D, hasta Virtualización KVM). Cada paquete tiene descripciones nativas. Tú eliges qué instalas pulsando la barra espaciadora.
- **Interfaz Gráfica en Terminal (TUI):** Desarrollada con la librería `Rich`, ofrece navegación interactiva, barras de progreso fluidas y paneles divisores (Splits) que muestran qué hace cada paquete en tiempo real.
- **Auto-Sanación (Self-Healing):** El motor intercepta errores críticos en vivo (bases de datos bloqueadas `pacman.lck`, errores de red, espejos caídos) y te despliega un menú para **Reintentar, Ignorar o Abortar**, salvando la instalación sin tener que empezar de cero.
- **Pre-purga Inteligente:** Detecta y destruye paquetes residuales y conflictivos en tu disco antes de instalar, evitando fallas silenciosas.

### 2. 🛡️ Arquitectura de Sincronización Híbrida 
Disfruta de lo último de Omarchy Oficial sin romper la estabilidad de CachyOS.
- **Filtro Negro Dinámico (Blacklist):** Nuestro código escanea las actualizaciones oficiales en tiempo real y **destruye en memoria** dependencias que dañarían tu sistema (ej. kernels genéricos de Ubuntu/Arch o paquetes inestables), protegiendo el núcleo ultra-optimizado de CachyOS.
- **Prioridad de Repositorios Inyectada:** El instalador reescribe tu `pacman.conf` para inyectar inteligentemente los servidores de Omarchy por encima de los demás, resolviendo automáticamente las guerras de paquetes (ej. garantizando que descargues siempre la barra oficial y no clones problemáticos).

### 3. ⚙️ Optimizaciones de Alto Nivel "Bajo el Capó"
Hemos operado el código fuente para resolver los dolores de cabeza de Linux:
- **Amputación de Polkit Zombie:** Solucionamos un *Crash* (Violación de Segmento) nativo del código C++ de Quickshell en Qt 6.11 aislando y destruyendo su plugin de contraseñas, delegándolo a un agente ultra-estable externo (`polkit-kde-agent`). **¡Cero ventanas de error azules!**
- **Soporte HiDPI (4K) Automático:** El instalador detecta e inyecta dinámicamente el flag `scale = "auto"` en Hyprland para que tus pantallas de alta resolución se vean perfectas desde el primer arranque.
- **Aceleración Gráfica VA-API:** Navegadores y aplicaciones preconfigurados para procesar video directo en tu tarjeta gráfica.

### 4. 🔄 El Actualizador Inmortal (Updater 2.0)
El mantenimiento de tu PC ahora vuela en piloto automático.
- **Auto-Migración (Rolling Release Real):** Al usar el botón "Actualizar" en el menú, el sistema no solo actualiza paquetes, sino que ejecuta docenas de scripts `.sh` de migración internos que **reescriben y modernizan tus archivos de configuración antiguos** para adaptarlos al código nuevo. Todo ocurre en segundos y evita que el entorno se rompa tras semanas sin actualizar.
- **Sistema de Auto-Salvado (Git Autostash):** Si personalizaste el código a mano (cambiaste colores, scripts, atajos), el actualizador **no** crasheará por un conflicto. Extraerá tus cambios, actualizará el núcleo oficial, y volverá a aplicar tus ediciones por encima automáticamente.
- **Permisos Reparados:** La arquitectura garantiza que la carpeta principal (`/usr/share/omarchy`) pertenezca a tu usuario, destrabando la actualización gráfica sin estancarse pidiendo contraseñas invisibles en segundo plano.

### 5. 🆘 El Sistema de Rescate TTY (Modo Supervivencia)
¿Tu tarjeta gráfica es vieja o tienes problemas con los drivers NVIDIA en Wayland?
- Si SDDM falla en arrancar, el sistema activa nuestro **Menú de Rescate en TTY** (vía Fish Shell).
- Te presenta una terminal estilizada donde con un solo número o letra puedes arrancar entornos seguros, hacer una purga profunda de caché, o forzar una reparación de pacman, todo sin teclear comandos complejos.

---

## 📥 Instalación (Un Solo Comando)

Para invocar el Mega Dashboard y comenzar la metamorfosis, ejecuta esto en un Live USB de CachyOS o en tu instalación base:

```bash
git clone -b quattro https://github.com/XzForz3-Dev/X64-Omarchy-CachyOS.git
cd X64-Omarchy-CachyOS
chmod +x x64-install.sh
./x64-install.sh
```
> [!IMPORTANT]
> **No uses `sudo`** para ejecutar el script. Nuestro **Security Gateway** tomará el control, desplegará una animación de escaneo y te pedirá tu contraseña de forma segura solo cuando sea estrictamente necesario.

---

## 🛠️ Entornos Soportados
Puedes instalar todos estos entornos simultáneamente. Nuestro *Chasis Puro* asegura que no se contaminen entre sí:
* 🌌 **Hyprland (Omarchy X64 Edition)** - La experiencia insignia.
* 🖥️ **KDE Plasma** - Robusto y clásico.
* 🍃 **Cinnamon** - Tradicional y veloz.
* 🪟 **Niri** - Para amantes de la estética scroll.

---
<div align="center">
  <b>Desarrollado y operado por X64 Studios.</b><br>
  <i>(Autores de la Arquitectura Híbrida, el Mega Dashboard TUI, el Security Gateway, los Motores de Auto-Sanación y las adaptaciones a hardware de CachyOS)</i><br>
  <br>
  <i>Inspirado y construido sobre la base arquitectónica de <a href="https://omarchy.org">Omarchy by DHH</a>.</i><br>
  <i>Impulsado por el núcleo ultra-optimizado de <a href="https://cachyos.org">CachyOS</a>.</i>
</div>
