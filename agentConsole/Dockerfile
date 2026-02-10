# Usar imagen oficial de Playwright (incluye Python y Browsers)
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de los tests
COPY . .

# Comando por defecto (puedes sobreescribirlo en el compose)
CMD ["pytest", "tests/test_calls.py"]
