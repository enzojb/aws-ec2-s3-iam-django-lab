# Arquitectura del Laboratorio Django + AWS EC2 + S3 + IAM

Este documento describe la arquitectura utilizada en el laboratorio y las decisiones técnicas tomadas para desplegar una aplicación Django en AWS con integración segura a servicios cloud.

El foco del diseño está puesto en la separación de responsabilidades, la seguridad por diseño y el uso correcto de servicios administrados de AWS.

---

## Visión general

La aplicación se ejecuta sobre una instancia EC2 y se integra con un bucket S3 privado para almacenamiento de archivos.

El acceso a AWS se realiza exclusivamente mediante IAM Roles, evitando el uso de credenciales estáticas.

---

## Componentes principales

### Servidor web (Nginx)

Nginx actúa como punto de entrada público al sistema.

Responsabilidades:
- Escuchar tráfico HTTP (puerto 80)
- Servir archivos estáticos
- Funcionar como reverse proxy hacia Gunicorn

Nginx es el único componente expuesto a Internet.

---

### Servidor de aplicaciones (Gunicorn)

Gunicorn es el servidor WSGI encargado de ejecutar la aplicación Django en producción.

Responsabilidades:
- Cargar la aplicación mediante `wsgi.py`
- Gestionar múltiples workers
- Manejar concurrencia de solicitudes

Gunicorn solo escucha en `127.0.0.1`, evitando exposición directa.

---

### Aplicación Django

La aplicación Django contiene la lógica de negocio del laboratorio.

Funciones principales:
- Recepción de archivos desde el frontend
- Validación de tamaño y formato (server-side, no confía en lo que declara el cliente)
- Delegación del almacenamiento a un servicio S3
- Generación de URLs prefirmadas para acceso temporal

La aplicación no contiene credenciales AWS embebidas. Sí exige su propia autenticación de sesión — ver "Autorización a nivel de aplicación" más abajo.

---

### Integración con AWS (boto3)

La comunicación con AWS se realiza mediante el SDK oficial **boto3**.

boto3:
- Obtiene credenciales automáticamente desde el Instance Metadata Service (IMDS)
- Firma las requests a los servicios AWS
- No requiere configuración manual de credenciales

---

### Almacenamiento (Amazon S3)

Se utiliza un bucket S3 privado para almacenar archivos subidos por la aplicación.

Características:
- Bucket sin acceso público
- Uso de prefijos (`images/`) para segmentar permisos
- Acceso a objetos mediante URLs prefirmadas

---

## Autenticación y permisos

La instancia EC2 tiene asociado un IAM Role con políticas de permisos mínimos.

Flujo de autenticación:
1. La EC2 asume un IAM Role
2. Obtiene credenciales temporales desde IMDS
3. boto3 utiliza esas credenciales para acceder a AWS
4. S3 valida los permisos definidos en la policy

No se utilizan access keys ni secretos embebidos en el código.

---

## Autorización a nivel de aplicación

El punto anterior describe la autenticación de **infraestructura** (la EC2 frente a AWS). Es un nivel distinto de la autenticación de **aplicación** (quién puede usar la app), y este laboratorio también la implementa:

- Las vistas de `uploads` (subir, listar, ver) requieren un usuario logueado (`@login_required`, sistema de auth estándar de Django — el mismo que ya protegía `/admin/`).
- Los archivos se referencian externamente por un identificador público (`public_id`, un UUID) en vez del id autoincremental de la base, para que no se puedan enumerar recorriendo `/files/1/`, `/files/2/`...
- El Content-Type y la extensión que llegan a S3 se derivan del contenido real del archivo (Pillow), no del nombre ni del header que manda el cliente.

## Principios de diseño aplicados

- Separación de responsabilidades
- Principio de mínimo privilegio
- Seguridad por diseño
- Infraestructura como parte del software
- Configuración explícita y documentada

---

## Decisiones de alcance del laboratorio

Algunas elecciones son deliberadas para el tamaño y el objetivo de este proyecto, no descuidos:

- **SQLite en vez de RDS**: la app corre en una sola instancia/proceso, sin escritura concurrente real que lo justifique. Migrar es directo (cambiar `DATABASES` por una base gestionada vía `dj-database-url`) pero no aporta nada a lo que este lab está demostrando.
- **Auth de sesión simple, sin modelo de ownership por usuario**: es un laboratorio de un solo operador (se crea un superusuario con `createsuperuser`). Un modelo multiusuario con `FK` a `User` por archivo sería sobre-ingeniería para lo que este proyecto necesita mostrar.
- **Rate limiting a nivel de Nginx, no de Django**: Gunicorn corre con varios workers (`--workers 3`); un límite en memoria a nivel de Django sería por-worker, no global, y daría una falsa sensación de protección. `limit_req` en Nginx sí es efectivo independientemente de cuántos workers haya detrás.

## Posibles extensiones

La arquitectura permite escalar hacia:
- CloudFront para distribución de contenido
- Terraform para IAM/Security Groups/VPC (hoy documentados en `docs/`, pero configurados a mano en la consola)
- Rate limiting distribuido (Redis) si la app corre en más de una instancia
- Separación de servicios por rol o instancia
- Migración a ECS o Lambda

---

## Conclusión

Este laboratorio representa una arquitectura típica de producción para aplicaciones Django en AWS, priorizando seguridad, claridad y mantenibilidad.