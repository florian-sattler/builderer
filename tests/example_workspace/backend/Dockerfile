FROM python:alpine

RUN pip install --no-cache 'redis==4.4.2' 'fastapi==0.89.1' 'uvicorn[standard]==0.20.0'
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
