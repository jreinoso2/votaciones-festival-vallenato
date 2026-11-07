# Sistema de votaciones - Festival de la Leyenda Vallenata 2027

Proyecto de la asignatura Desarrollo Web (Fundación Universitaria del Área Andina).
**Entrega 3:** módulo de votaciones, validaciones y API GET.

Aplicación web hecha con **Python 3.12, Django 5.2 (patrón MVT) y MySQL 8.4**.

## Funcionalidades

**Entrega 2**
- Registro, inicio y cierre de sesión (autenticación de Django; las contraseñas se guardan con función hash PBKDF2-SHA256 y sal, nunca en texto plano).
- Administración de ediciones, categorías, votaciones (subeventos) y opciones con Django Admin.
- Consulta pública de ediciones → categorías → votaciones → opciones desde MySQL.

**Entrega 3**
- Registro de votos en dos pasos: seleccionar opción → confirmar → guardar en MySQL.
- Regla de unicidad: **un voto por usuario, categoría y edición**, aunque la categoría tenga varios subeventos. Se puede votar en otras categorías.
- Validaciones en el servidor: sesión iniciada, votación abierta y dentro de sus fechas, opción que pertenece a la votación, protección CSRF, voto solo por POST.
- Protección ante solicitudes simultáneas: índice `UNIQUE (usuario, categoria, edicion)` en MySQL y manejo de `IntegrityError`.
- Página **Mis votos** con las categorías en que participó el usuario.
- Consulta administrativa de votos (solo lectura) y total de votos por opción en Django Admin.
- API **GET `/api/categorias/`** con las categorías, sus votaciones y opciones en JSON.

## Dónde está cada cosa

| Elemento | Archivo |
|----------|---------|
| Modelo `Voto` y restricción de unicidad | `votaciones/models.py` (clase `Voto`, `UniqueConstraint` `voto_unico_usuario_categoria_edicion`) |
| Migración del modelo de votos | `votaciones/migrations/0002_voto.py` |
| Validaciones y control de duplicados | `votaciones/servicios.py` (`validar_voto`, `registrar_voto`) |
| Vistas de voto, historial y API | `votaciones/views.py` (`confirmar_voto`, `registrar`, `mis_votos`, `api_categorias`) |
| Rutas | `votaciones/urls.py` |
| Administración de votos | `votaciones/admin.py` (`VotoAdmin`) |
| Pruebas CP-01 a CP-10 | `votaciones/tests.py` |
| Datos de prueba | `votaciones/management/commands/cargar_datos_demo.py` |

## Estructura

```
votaciones_festival/
├── festival/      # configuración del proyecto (settings, urls)
├── votaciones/    # modelos, vistas, servicios (reglas), plantillas, admin, pruebas y API
├── usuarios/      # registro, login y logout
└── templates/     # plantilla base.html
```

## Requisitos

- Python 3.12
- MySQL 8 (probado con 8.4)
- Dependencias de `requirements.txt`: Django 5.2.18, mysqlclient 2.3.0, python-dotenv 1.2.4

## Instalación y ejecución

1. Clonar el repositorio:
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
   Para ejecutar las pruebas, el usuario de MySQL debe tener permiso para crear la base temporal `test_votaciones_festival`.
5. Copiar `.env.example` como `.env` y escribir el usuario y la contraseña de MySQL de su equipo. El `.env` real **no** se sube al repositorio.
6. Aplicar las migraciones:
   ```
   python manage.py migrate
   ```
7. Cargar los datos de prueba (ficticios):
   ```
   python manage.py cargar_datos_demo
   ```
   Crea las ediciones 2026 y 2027, sus categorías, votaciones y opciones, y dos usuarios votantes de prueba: `votante1` y `votante2` (contraseña `Festival2027*`, solo para pruebas locales).
8. Crear el usuario administrador:
   ```
   python manage.py createsuperuser
   ```
9. Iniciar el servidor:
   ```
   python manage.py runserver
   ```
10. Abrir en el navegador:
    - Sitio público: http://127.0.0.1:8000/
    - API: http://127.0.0.1:8000/api/categorias/
    - Administración: http://127.0.0.1:8000/admin/

## Pruebas automáticas

```
python manage.py test votaciones -v 2
```

| Caso | Prueba en `votaciones/tests.py` |
|------|---------------------------------|
| CP-01 Voto válido se registra | `test_cp01_voto_valido_se_registra` |
| CP-02 Segundo voto en la misma categoría (otra opción u otro subevento) | `test_cp02_segundo_voto_misma_categoria_rechazado` |
| CP-03 Voto en otra categoría | `test_cp03_voto_en_otra_categoria_permitido` |
| CP-04 Usuario sin sesión | `test_cp04_usuario_no_autenticado_debe_iniciar_sesion` |
| CP-05 Votación cerrada o vencida | `test_cp05_categoria_no_habilitada_rechazada` |
| CP-06 Opción de otra categoría | `test_cp06_opcion_de_otra_categoria_rechazada` |
| CP-07 Mis votos | `test_cp07_usuario_consulta_sus_votos` |
| CP-08 Consulta del administrador | `test_cp08_administrador_consulta_votos` |
| CP-09 Solicitudes simultáneas | `test_cp09_solicitudes_simultaneas_un_solo_voto`, `test_cp09_restriccion_unique_de_mysql` |
| CP-10 API GET JSON | `test_cp10_api_categorias_json` |
| Seguridad extra | `test_csrf_obligatorio`, `test_votar_por_get_no_permitido` |

## Rutas

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Lista de ediciones |
| `/edicion/<año>/` | GET | Categorías de una edición (marca las ya votadas) |
| `/categoria/<id>/` | GET | Votaciones (subeventos) de una categoría |
| `/votacion/<id>/` | GET | Opciones de una votación y formulario de voto |
| `/votacion/<id>/confirmar/` | POST | Valida la opción y muestra la confirmación (requiere sesión) |
| `/votacion/<id>/votar/` | POST | Valida otra vez y guarda el voto (requiere sesión) |
| `/mis-votos/` | GET | Historial de votos del usuario (requiere sesión) |
| `/api/categorias/` | GET | API JSON de categorías, votaciones y opciones. Filtro opcional `?edicion=2027` |
| `/usuarios/registro/` | GET/POST | Registro |
| `/usuarios/login/` | GET/POST | Iniciar sesión |
| `/usuarios/logout/` | POST | Cerrar sesión |
| `/admin/` | GET | Django Admin (incluye la consulta de votos) |

### Ejemplo de respuesta de la API

```json
{
  "total": 5,
  "categorias": [
    {
      "id": 1,
      "nombre": "Acordeón Profesional",
      "edicion": {"id": 2, "anio": 2027, "nombre": "Festival de la Leyenda Vallenata"},
      "votaciones": [
        {
          "id": 1,
          "titulo": "Acordeonero favorito del público",
          "estado": "abierta",
          "habilitada": true,
          "opciones": [{"id": 1, "nombre": "Participante A", "descripcion": "..."}]
        }
      ]
    }
  ]
}
```

## Equipo

PENDIENTE: nombres completos de los cuatro integrantes.
