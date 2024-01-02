
# Billetera Virtual - Proyecto Django

Este proyecto de Billetera Virtual es una aplicación web desarrollada con el framework Django. Permite a los usuarios realizar un seguimiento de sus gastos personales, crear nuevos gastos, editar y eliminar gastos existentes.

## Funcionalidades Principales

- Lista de Gastos: Muestra una lista de todos los gastos registrados.
- Crear Gasto: Permite a los usuarios agregar nuevos gastos a su billetera.
- Editar Gasto: Los usuarios pueden editar los detalles de un gasto existente.
- Eliminar Gasto: Permite a los usuarios eliminar un gasto de su lista.

## Requisitos

- Python 3.x
- Django 4.2 (Instalado automáticamente con el entorno virtual)

## Instalación y Configuración

1. Clona este repositorio en tu máquina local:

```
git clone <URL_del_repositorio>
```

2. Crea un entorno virtual para el proyecto:

```
python3 -m venv myenv
```

3. Activa el entorno virtual:

```
source myenv/bin/activate
```

4. Instala las dependencias del proyecto:

```
pip install -r requirements.txt
```

5. Realiza las migraciones de la base de datos:

```
python manage.py migrate
```

6. Crea un superusuario (admin) para acceder al panel de administración:

```
python manage.py createsuperuser
```

7. Inicia el servidor de desarrollo:

```
python manage.py runserver
```

8. Accede a la aplicación en tu navegador web:

```
http://127.0.0.1:8000/
```


9. Para acceder al panel de administración, utiliza las credenciales del superusuario que creaste en el paso 6:

```
http://127.0.0.1:8000/admin/
```

## Uso

- Registra tus gastos personales en la aplicación.
- Visualiza la lista de gastos.
- Edita los detalles de un gasto si es necesario.
- Elimina gastos que ya no necesites.

## Contribuciones

Si deseas contribuir a este proyecto, ¡te damos la bienvenida! Siéntete libre de crear problemas (issues) o enviar solicitudes de extracción (pull requests).

