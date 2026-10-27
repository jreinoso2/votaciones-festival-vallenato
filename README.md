# Sistema de votaciones - Festival de la Leyenda Vallenata 2027

Proyecto de la asignatura Desarrollo Web (Fundación Universitaria del Área Andina) - Entrega 2.

Aplicación web hecha con **Python, Django (patrón MVT) y MySQL**.

## Funcionalidades de esta entrega

- Registro, inicio de sesión y cierre de sesión (sistema de autenticación de Django).
- Administración de ediciones, categorías, votaciones y opciones con Django Admin.
- Páginas públicas que muestran los datos guardados en MySQL:
  ediciones → categorías → votaciones → opciones.

## Estructura

```
votaciones_festival/
├── festival/      # configuración del proyecto (settings, urls)
├── votaciones/    # app: modelos Edicion, Categoria, Votacion, Opcion, vistas y plantillas
├── usuarios/      # app: registro, login y logout
└── templates/     # plantilla base.html
```

## Requisitos

- Python 3.12
- MySQL 8

## Instalación y ejecución

1. Clonar el repositorio y entrar a la carpeta:
   ```
   git clone https://github.com/jreinoso2/votaciones-festival-vallenato.git
   cd votaciones-festival-vallenato
   ```
2. Crear y activar el entorno virtual:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Crear la base de datos en MySQL:
   ```sql
   CREATE DATABASE votaciones_festival CHARACTER SET utf8mb4;
   ```
5. Copiar `.env.example` como `.env` y poner el usuario y la contraseña de MySQL.
6. Ejecutar las migraciones:
   ```
   python manage.py migrate
   ```
7. Crear el usuario administrador:
   ```
   python manage.py createsuperuser
   ```
8. Iniciar el servidor:
   ```
   python manage.py runserver
   ```
9. Abrir en el navegador:
   - Sitio público: http://127.0.0.1:8000/
   - Administración: http://127.0.0.1:8000/admin/

## Rutas

| Ruta | Descripción |
|------|-------------|
| `/` | Lista de ediciones |
| `/edicion/<año>/` | Categorías de una edición |
| `/categoria/<id>/` | Votaciones de una categoría |
| `/votacion/<id>/` | Detalle y opciones de una votación |
| `/usuarios/registro/` | Registro |
| `/usuarios/login/` | Iniciar sesión |
| `/usuarios/logout/` | Cerrar sesión |
| `/admin/` | Django Admin |

## Autor

- [Nombre completo]
