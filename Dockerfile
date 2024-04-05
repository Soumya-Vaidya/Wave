FROM python:3

WORKDIR /Wave

COPY App/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python","app.py"]