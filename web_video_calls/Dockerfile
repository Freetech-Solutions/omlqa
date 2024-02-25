# Usar una imagen base oficial de Python
FROM python:3.9

# Establecer el directorio de trabajo en el contenedor
WORKDIR /usr/src/app

# Copiar los requisitos de archivo
COPY requirements.txt ./
# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

EXPOSE 8889

# Establecer variables de entorno necesarias para Flask
ENV FLASK_APP=webphone.py
ENV FLASK_DEBUG=1

# Comando para ejecutar la aplicación Flask con SSL ad-hoc
CMD ["flask", "run", "--host=0.0.0.0", "--cert=adhoc"]
