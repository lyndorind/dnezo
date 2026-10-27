# Етап 1: Збірка (Build stage)
FROM python:3.11-slim AS builder
WORKDIR /app

# Копіюємо файл із залежностями
COPY requirements.txt .

# Встановлюємо залежності у локальну директорію
RUN pip install --user --no-cache-dir -r requirements.txt

# Етап 2: Робоче середовище (Runtime stage)
FROM python:3.11-slim
WORKDIR /app

# Копіюємо лише встановлені залежності з попереднього етапу
COPY --from=builder /root/.local /root/.local

# Копіюємо решту файлів проєкту
COPY . .

# Налаштовуємо змінні середовища
ENV PATH=/root/.local/bin:$PATH
ENV FLASK_APP=medical_app.py

EXPOSE 8080
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8080"]