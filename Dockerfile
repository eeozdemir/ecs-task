FROM python:3-alpine
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt
CMD ["python3", "src/app.py"]