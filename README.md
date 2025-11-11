
-----

# Gestión de Inventario para Tienda Online (CRUD Avanzado)

Esta aplicación web construida con **Django** proporciona una plataforma robusta para la gestión completa del inventario de una tienda online, implementando operaciones CRUD avanzadas y un sistema de seguridad granular basado en permisos de grupo.

-----

## Descripción y Características Principales

El núcleo de la aplicación se centra en la administración de un catálogo de **Productos**, complementado con entidades de clasificación (`Categoría` y `Etiqueta`) y un módulo de detalles físicos (`DetalleProducto`).

  * **CRUD Completo:** Implementación de las cuatro operaciones esenciales (Crear, Leer, Actualizar y Eliminar) para Productos, Categorías y Etiquetas.
  * **Integridad de Datos:** Restricción de unicidad en el nombre del producto y validaciones estrictas (ej. peso o precio deben ser mayores a cero).
  * **Seguridad por Roles:** El acceso a funciones críticas (Creación, Edición y Eliminación) está controlado por permisos asignados a grupos de usuarios.
  * **Consultas Avanzadas:** Se incluyen filtros dinámicos en la interfaz y reportes generados con lógica de ORM y sentencias SQL personalizadas.

-----

## Requisitos e Instalación

### Dependencias

El proyecto utiliza **Python** y **Django** como framework principal, y se conecta a una base de datos **MySQL**.

Para instalar todas las dependencias necesarias, asegúrese de tener activo su entorno virtual y ejecute el siguiente comando:

```bash
pip install -r requirements.txt
```

### Configuración Inicial

Una vez instaladas las dependencias, la base de datos debe inicializarse:

1.  **Migraciones:** Aplique las migraciones para crear todas las tablas, incluyendo las relaciones y las restricciones de unicidad.
    ```bash
    python manage.py migrate
    ```
2.  **Superusuario:** Cree un superusuario para acceder al panel de administración y gestionar permisos.
    ```bash
    python manage.py createsuperuser
    ```
3.  **Grupos de Permisos:** Es esencial crear los siguientes grupos en el Panel de Administración de Django para que el sistema de seguridad funcione correctamente:
      * `Administradores`
      * `Gestión`
      * `Clientes`

-----

## Arquitectura y Flujo de Gestión (CRUD)

### 1\. Modelado de Datos

El sistema utiliza las siguientes relaciones para la integridad del inventario:

  * **Relación Muchos a Uno (Categoría):** Un `Producto` pertenece a una única `Categoría`. **(Regla: Obligatorio)**
  * **Relación Muchos a Muchos (Etiquetas):** Un `Producto` puede tener múltiples `Etiquetas`. **(Regla: Obligatorio)**
  * **Relación Uno a Uno (Detalles):** Un `Producto` tiene un conjunto único de `Detalles Físicos` (dimensiones, peso).
  * **Relación M:M (Favoritos):** El modelo `Producto` está asociado a la lista de **Favoritos** de los usuarios.

### 2\. Flujo de Creación (Dependencia Crítica)

Para mantener la integridad referencial, el flujo de trabajo para crear un producto es estricto:

> **ATENCIÓN:** Antes de crear un **Producto**, deben existir previamente las **Categorías** y **Etiquetas** a las que se asociará, ya que el producto **no puede ser creado sin ellas**.

  * **Gestión Simple (CBV):** Las vistas para crear y editar **Categorías** y **Etiquetas** utilizan **Vistas Basadas en Clases (`CreateView`, `UpdateView`)**.
  * **Gestión Compleja (FBV):** La creación y edición de **Productos** utiliza **Vistas Basadas en Funciones (FBV)**, debido a la manipulación de un **Formset** (`DetalleProductoFormset`) y la lógica de transacción atómica.

### 3\. Integridad de Borrado (`models.PROTECT`)

El sistema implementa restricciones de borrado para proteger el inventario:

  * **Eliminar Categoría:** Utiliza **`on_delete=models.PROTECT`**. Si se intenta eliminar una Categoría que tiene productos asociados, el sistema **bloqueará la acción** y mostrará un mensaje de error claro (no permitirá que se rompa la base de datos).
  * **Eliminar Etiqueta:** Dado que es una relación Muchos-a-Muchos, la eliminación de la etiqueta solo **desvincula la etiqueta** del producto (no elimina el producto).

-----

## Sistema de Permisos y Roles

La aplicación utiliza la funcionalidad `django.contrib.auth` para el control de acceso.

### Asignación de Usuarios

1.  **Registro Automático:** Los nuevos usuarios registrados a través del *frontend* son asignados automáticamente al grupo **`Clientes`**.
2.  **Elevación de Permisos:** Los roles `Gestión` y `Administradores` deben ser asignados manualmente a través del **Panel de Administración** (`/admin/`).

### Niveles de Acceso y Permisos

| Grupo | Funcionalidad | Control de Acceso |
| :--- | :--- | :--- |
| **Administradores** | **Acceso Total (CRUD + D)**. Elimina cualquier entidad. | $\text{delete\_producto}$, $\text{delete\_categoria}$, etc. |
| **Gestión** | **CRUD Parcial (CRU sin D)**. **No puede** eliminar ninguna entidad. | $\text{add/change/view}$ (Restringido de $\text{delete}$). |
| **Clientes** | **Solo Lectura (R)** y **Funcionalidad de Favoritos**. | $\text{view}$ nativo + acceso a la vista `toggle_favorito`. |

-----

## ✨ Estética y Usabilidad (Crispy Forms)

El proyecto utiliza la librería **django-crispy-forms** para mejorar la experiencia de usuario y optimizar el desarrollo de formularios:

  * **Diseño Unificado:** Los formularios (CRUD y Autenticación) se renderizan con el paquete **Bootstrap 5**, asegurando una apariencia moderna y consistente.
  * **Optimización HTML:** Los formularios complejos (como el de Producto) se dibujan en el *frontend* con una sola etiqueta `{{ form|crispy }}`.
  * **Validación de UX:** Se desactiva el molesto asterisco (`*`) de los campos obligatorios y se utiliza la validación nativa HTML5, manteniendo un diseño limpio y profesional.

-----

## Cumplimiento de Requisitos y Elementos Extras

| Requisito Avanzado | Implementación Específica |
| :--- | :--- |
| **Productos Favoritos** | Implementación de **`ManyToManyField`** entre `User` y `Producto` y una vista **`toggle_favorito`** para que los clientes puedan gestionar su lista privada. |
| **Consultas Avanzadas ORM** | Filtros dinámicos por nombre, categoría y **precio mayor que (`__gt`)** en la interfaz de listado. |
| **SQL Personalizado** | Generación del reporte **Auditoría de Clasificación de Inventario** (`raw()` + `GROUP_CONCAT`) para consolidar etiquetas y categorías en un solo reporte. |
| **Control UX** | El botón **Eliminar** se oculta del *frontend* para el rol **Gestión**, manteniendo la coherencia visual con sus permisos. |
| **Validación Estricta** | El precio (`DecimalField`) y peso tienen validadores (`MinValueValidator`) para asegurar valores positivos. |

-----

## 💻 Puesta en Marcha

Una vez completada la configuración, inicie la aplicación:

```bash
python manage.py runserver
```

Acceda a `http://127.0.0.1:8000/` y pruebe las restricciones de roles para una validación final.