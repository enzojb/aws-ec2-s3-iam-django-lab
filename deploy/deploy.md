# Despliegue en Producción (EC2 + Nginx + Gunicorn)

Este proyecto fue desplegado en una instancia **AWS EC2** utilizando una arquitectura estándar de producción para aplicaciones Python/Django.

El objetivo de este despliegue es demostrar un entorno real, estable y seguro, separando correctamente responsabilidades entre servidor web, servidor de aplicaciones y lógica de negocio.

Los archivos de esta carpeta son **plantillas de referencia** y no forman parte del código ejecutable del proyecto.

---

## Arquitectura general

Internet → Nginx (puerto 80) → Gunicorn (WSGI - localhost:8000) → Aplicación Django

---

## Requisitos del servidor

- Ubuntu 20.04 o superior (probado en Ubuntu 22.04)
- Python 3.10
- virtualenv
- Nginx
- systemd

---

## Entorno virtual de Python

Se utiliza un entorno virtual para aislar dependencias del sistema:

```bash
python3 -m venv /var/www/awsLab/venv
source /var/www/awsLab/venv/bin/activate
pip install -r /var/www/awsLab/requirements.txt
```

Este enfoque evita conflictos entre proyectos y es una práctica recomendada en entornos productivos.

## Gunicorn (servidor de aplicaciones)

Gunicorn se utiliza como servidor WSGI para ejecutar la aplicación Django en producción.

Se ejecuta como un servicio de systemd, lo que permite:

- inicio automático al arrancar el sistema
- reinicio ante fallos
- centralización de logs

Archivo de referencia:

- gunicorn.service.example

Pasos de instalación:

```bash
sudo cp deploy/gunicorn.service.example /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
```

Gunicorn escucha únicamente en 127.0.0.1, evitando la exposición directa de la aplicación a Internet.

## Nginx (servidor web y reverse proxy)

Nginx actúa como servidor web frontal y reverse proxy.

Sus responsabilidades incluyen:

- recibir el tráfico HTTP público
- servir archivos estáticos
- reenviar las solicitudes a Gunicorn

Archivo de referencia:

- nginx.awsLab.example

Pasos de instalación:

```bash
sudo cp deploy/nginx.awsLab.example /etc/nginx/sites-available/awsLab
sudo ln -s /etc/nginx/sites-available/awsLab /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Archivos estáticos

Los archivos estáticos se recolectan mediante:

- python manage.py collectstatic

Nginx los sirve directamente desde el directorio staticfiles/, evitando que Gunicorn o Django los procesen.

## HTTPS/TLS con Let's Encrypt (certbot)

`nginx.awsLab.example` ya trae dos server blocks: el primero (puerto 80) redirige todo a HTTPS, el segundo (443) termina TLS. Para emitir el certificado:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

certbot instala el certificado, reescribe `ssl_certificate`/`ssl_certificate_key` en el server block y configura la renovación automática vía el timer de systemd (`certbot.timer`), sin pasos manuales adicionales.

**Nota:** Let's Encrypt exige un nombre de dominio — no emite certificados para una IP pública sola. Para probar esto hace falta un dominio (o subdominio) apuntando al Elastic IP de la instancia.

Una vez emitido el certificado, en `.env` seteá `ENV=production` para que Django active `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` y HSTS (ver `awsLab/settings.py`).

## Variables de entorno en producción

Además de las que ya trae `.env.example`, en el servidor real conviene setear:

```bash
ALLOWED_HOSTS=your-domain.com
ADMIN_URL=panel-interno/
```

## Consideraciones de seguridad

- El servidor de desarrollo de Django (runserver) no se utiliza en producción

- Gunicorn no es accesible desde Internet

- Nginx es el único punto de entrada público

- Todo el tráfico se sirve por HTTPS (redirect 80→443, certificado de Let's Encrypt)

- Nginx aplica rate limiting (`limit_req`) sobre `/upload/`

- El despliegue sigue una separación clara de responsabilidades

## Notas finales

Este despliegue representa una configuración típica utilizada en entornos de producción para aplicaciones Django, priorizando estabilidad, seguridad y mantenibilidad.