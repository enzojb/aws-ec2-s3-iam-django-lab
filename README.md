# Django + AWS EC2 + S3 + IAM — Laboratorio de integración Cloud

Este proyecto es un **laboratorio práctico** que demuestra el despliegue de una aplicación **Django en producción sobre AWS**, integrando servicios cloud reales con buenas prácticas de arquitectura, seguridad y operación.

El objetivo del lab no es la aplicación en sí, sino **mostrar cómo desplegar, operar e integrar una app Python con AWS de forma profesional**.

---

## 🎯 Objetivos del laboratorio

- Desplegar una aplicación Django en una instancia **EC2**
- Configurar **Nginx** como servidor web y reverse proxy
- Ejecutar Django en producción con **Gunicorn**
- Integrar **Amazon S3** para almacenamiento de archivos
- Autenticar la aplicación con AWS mediante **IAM Roles** (sin access keys)
- Aplicar el principio de **mínimo privilegio**
- Generar **URLs prefirmadas** para acceso seguro a objetos privados

---

## 🏗️ Arquitectura general

Usuario / Navegador → Nginx (HTTP :80) → Gunicorn (WSGI :8000) → Django → boto3 → Amazon S3 (bucket privado)

---

## ⚙️ Stack tecnológico

- **Backend:** Django (Python)
- **Servidor web:** Nginx
- **Servidor de aplicaciones:** Gunicorn
- **Infraestructura:** AWS EC2
- **Almacenamiento:** Amazon S3
- **Autenticación AWS:** IAM Roles + Instance Metadata Service (IMDSv2)
- **SDK AWS:** boto3
- **Sistema operativo:** Ubuntu

---

## 🚀 Funcionalidades del laboratorio

- Autenticación de sesión para acceder a la app (subir, listar, descargar)
- Subida de archivos desde la aplicación web, con validación de tamaño y formato
- Almacenamiento de archivos en un bucket S3 privado
- Listado de archivos almacenados
- Acceso a archivos mediante **URLs prefirmadas**, identificadas con un UUID no adivinable
- Sin uso de credenciales estáticas en el código

---

## 🔐 Seguridad

El diseño prioriza seguridad desde la arquitectura:

- ❌ No se utilizan `AWS_ACCESS_KEY_ID` ni `AWS_SECRET_ACCESS_KEY`
- ✅ Autenticación mediante **IAM Role asociado a la EC2**
- ✅ Credenciales temporales gestionadas por AWS
- ✅ Permisos limitados a un prefijo específico del bucket (`images/*`)
- ✅ Bucket S3 completamente privado
- ✅ Acceso temporal a objetos mediante URLs prefirmadas

Este enfoque reduce el riesgo de filtración de credenciales y se alinea con las
prácticas recomendadas para entornos productivos en AWS.

A nivel de aplicación (no solo de infraestructura):

- ✅ Autenticación de sesión requerida para subir, listar y descargar (`login_required`)
- ✅ Identificadores públicos no adivinables (UUID) en vez de IDs autoincrementales
- ✅ Validación de tamaño y formato de archivo server-side, sin confiar en el Content-Type del cliente
- ✅ HTTPS/TLS vía Nginx + certbot, con `SECURE_SSL_REDIRECT`/HSTS activados en producción
- ✅ Rate limiting en Nginx sobre el endpoint de subida
- ✅ Ruta de `/admin/` configurable por variable de entorno en vez de fija

---

## 🧪 Variables de entorno

Las variables sensibles no se incluyen en el repositorio.

Ejemplo (`.env.example`):

```bash
ENV=local
DEBUG=False
SECRET_KEY=secret-key

ALLOWED_HOSTS=127.0.0.1,localhost
ADMIN_URL=admin/
MAX_UPLOAD_SIZE_MB=5

AWS_REGION=us-east-1
AWS_S3_BUCKET=bucket-name
S3_PREFIX=images/
```

En producción, `ALLOWED_HOSTS` pasa a ser el dominio real y `ADMIN_URL` conviene cambiarlo a algo no adivinable (ver `deploy/deploy.md`).

## ☁️ AWS Setup (resumen)

EC2 con un IAM Role asociado

IAM Policy con permisos mínimos:

- s3:PutObject, s3:GetObject, s3:DeleteObject sobre images/*

- s3:ListBucket limitado al prefijo

- S3 Bucket privado, sin acceso público

El SDK boto3 obtiene las credenciales automáticamente desde el Instance Metadata Service (IMDSv2).

## 📚 Documentación técnica

La carpeta docs/ contiene documentación técnica adicional que explica las decisiones de arquitectura y seguridad tomadas durante el desarrollo del laboratorio.

Incluye:

- architecture.md
Describe la arquitectura general del sistema, los componentes involucrados y los principios de diseño aplicados.

- iam-policy.json
Policy de referencia utilizada para el IAM Role asociado a la instancia EC2, mostrando una configuración de permisos mínimos para acceso a S3.

## 📄 Despliegue

El despliegue en producción se documenta en detalle en la carpeta:

- deploy/

Allí se incluyen:

- Servicio systemd para Gunicorn

- Configuración de Nginx como reverse proxy

- Explicación paso a paso del entorno productivo

## ▶️ Ejecución local (desarrollo)

El proyecto puede ejecutarse localmente con fines de desarrollo y prueba.

### Comenzar con:

```bash
git clone https://github.com/enzojb/aws-ec2-s3-iam-django-lab.git

cd aws-ec2-s3-iam-django-lab
```

### Entrar al proyecto Django (donde está manage.py)
```bash
cd awsLab

python -m venv venv
```

### A. En Linux / macOS
```bash
source venv/bin/activate
```

### B. En Windows
```bash
source venv/Scripts/activate
```

### Luego
```bash
pip install -r ./requirements.txt

cp ./.env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

La app ahora exige login (ver sección Seguridad) — `createsuperuser` crea el usuario con el que vas a entrar.

### Finalmente acceder a:

http://127.0.0.1:8000/

## 🧠 Aprendizajes clave

Este laboratorio demuestra conocimientos en:

- Despliegue de aplicaciones Python en producción

- Separación de responsabilidades (Nginx / Gunicorn / Django)

- Autenticación segura en AWS

- Uso profesional de IAM Roles

- Integración real con servicios cloud

- Seguridad por diseño, no por parches

## 📌 Notas finales

Este proyecto está pensado como un laboratorio técnico demostrativo, no como una aplicación final de negocio. El foco está puesto en la infraestructura, la integración cloud y las buenas prácticas de despliegue.