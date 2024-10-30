# 💸 Billetera Virtual - Proyecto Django 🐍💻

💸 **Billetera Virtual** es una aplicación 🌐 desarrollada con Django 🐍 que permite a los usuarios 👥 gestionar sus finanzas 💰 personales. Los usuarios pueden realizar un seguimiento 📊 de sus ingresos 📈 y gastos 💸, categorizar sus movimientos 📁 y mantener un control eficiente de su presupuesto (En desarrollo 🚧).

## ⚙️ Funcionalidades Principales 🔧

- **💸 Gastos**:

  - 📋 Lista de Gastos: Visualiza 👀 todos los gastos registrados.
  - ➕ Crear Gasto: Agrega nuevos gastos, especificando descripción 📝, monto 💲, moneda 💵 y categoría 📊.
  - ✏️ Editar Gasto: Modifica los detalles de un gasto existente.
  - 🗑️ Eliminar Gasto: Elimina gastos registrados.

- **📈 Ingresos**:

  - 📋 Lista de Ingresos: Visualiza todos los ingresos registrados.
  - ➕ Crear Ingreso: Registra nuevos ingresos, especificando detalles como monto 💲 y categoría 📊.
  - ✏️ Editar Ingreso: Actualiza los detalles de ingresos existentes.
  - 🗑️ Eliminar Ingreso: Permite eliminar ingresos si es necesario.

- **💱 Monedas y Categorías**:

  - 💵 Monedas: Permite utilizar diferentes monedas 💰 para ingresos 📈 y gastos 💸.
  - 📊 Categorías: Organiza ingresos 📈 y gastos 💸 con categorías para un mejor seguimiento.

- **👤 Perfil de Usuario**:

  - 🔐 Registro y Autenticación: Los usuarios pueden registrarse ✍️, iniciar sesión 🔑 y gestionar su perfil 🖋️.

## ⚙️ Requisitos 📋

- 🐍 Python 3.x ([Documentación oficial](https://www.python.org/doc/))
- 🐍 Django 4.2 (se instala junto con las dependencias del entorno virtual 🌐) ([Documentación oficial](https://docs.djangoproject.com/en/stable/))

## 🚀 Instalación y Configuración ⚙️

1. 🌀 Clona este repositorio en tu máquina local 🖥️:

   ```
   git clone <URL_del_repositorio>
   ```

2. 🔧 Crea un entorno virtual para el proyecto:

   ```
   python3 -m venv myenv
   ```

3. 🚀 Activa el entorno virtual:

   - 🐧 En Linux/macOS:
     ```
     source myenv/bin/activate
     ```
   - 🪟 En Windows:
     ```
     myenv\Scripts\activate
     ```

4. 📦 Instala las dependencias del proyecto:

   ```
   pip install -r requirements.txt
   ```

5. ⚒️ Realiza las migraciones de la base de datos 🗃️ para preparar la estructura:

   ```
   python manage.py migrate
   ```

   > **Nota:** Si encuentras problemas durante la migración (como errores de permisos), verifica que tengas las dependencias correctamente instaladas y permisos adecuados para ejecutar comandos de Django.

6. 🔑 Crea un superusuario (admin 👑) para acceder al panel de administración:

   ```
   python manage.py createsuperuser
   ```

7. 🚀 Inicia el servidor de desarrollo 🌐:

   ```
   python manage.py runserver
   ```

8. 🌍 Accede a la aplicación en tu navegador web 🖥️:

   ```
   http://127.0.0.1:8000/
   ```

9. 🔒 Para acceder al panel de administración 🛠️, utiliza las credenciales del superusuario:

   ```
   http://127.0.0.1:8000/admin/
   ```

## 📝 Uso 💡

- **📊 Registro de Gastos e Ingresos**: Puedes registrar ingresos 📈 y gastos 💸 con sus respectivas categorías 📁 y monedas 💱, permitiendo un control claro de tus finanzas 💰.
- **👀 Visualización y ✏️ Edición**: Consulta y edita tus gastos 💸 e ingresos 📈 para mantener la información actualizada 🔄 y organizada 📂.
- **📋 Panel de Usuario**: Accede a tu panel de control 🕹️ para obtener una visión general de tus finanzas 📊.

## 🤝 Contribuciones 💪

Si deseas contribuir a este proyecto, serás bienvenido 🤗. Puedes abrir **issues** para reportar problemas ⚠️ o sugerencias 💡 y realizar **pull requests** con mejoras ✨ o nuevas funcionalidades 🚀.

## 📜 Licencia ⚖️

Este proyecto está bajo la licencia MIT 📝. Siéntete libre de usar, modificar 🔄 y distribuir el código 💻.

> **Nota:** Para más detalles sobre las licencias y su elección, puedes consultar la [guía de licencias de software](https://choosealicense.com/).

