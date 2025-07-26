FROM python:3.11-slim
LABEL "language"="python"
WORKDIR /
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "/web/app.py"]