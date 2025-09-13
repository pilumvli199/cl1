FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip && pip install -r requirements.txt
ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "src.app.tasks.main:app", "--host", "0.0.0.0", "--port", "8000"]
