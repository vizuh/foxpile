FROM python:3.10-slim-bullseye

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./*.py /code/
COPY ./.env /code/.env

# 
CMD ["python", "foxpile_main.py"]