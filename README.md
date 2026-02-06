# Personal Automate Monorepo

Este repositorio centraliza mis proyectos de desarrollo personal, abarcando áreas como:
- **Data Science**: Procesamiento y visualización de datos.
- **Geometría y 3D**: Manipulación de archivos STL y algoritmos geométricos.
- **Computer Vision**: Scripts de visión por computador.
- **Automatización**: Scripts para tareas repetitivas e inventario.

## Estructura

- `projects/`: Contiene el código fuente de los diferentes proyectos.
- `notebooks/`: Jupyter Notebooks para exploración y pruebas (Sandbox).
- `data/`: Datos de entrada y salida (ignorado en git salvo excepciones).
- `src/`: Código compartido y utilidades.
- `docs/`: Documentación general.

## Gestión de Dependencias

Este proyecto utiliza `uv` para la gestión de dependencias y entornos virtuales.

### Instalación

Si no tienes `uv` instalado, instálalo primero:
```bash
pip install uv
```

Para instalar las dependencias del proyecto:
```bash
uv sync
```

### Ejecución

Para ejecutar scripts utilizando el entorno virtual gestionado por `uv`:

```bash
uv run projects/inventory/procesador_gui.py
```

## Proyectos Destacados

- **Inventory**: Procesador de reportes de inventario `Fran`.
- **Geometry**: Herramientas para manipulación de mallas.
