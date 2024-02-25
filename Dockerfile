FROM python:3.10-slim-bullseye

RUN apt-get update
RUN apt-get -y install libleptonica-dev tesseract-ocr libtesseract-dev python3-pil tesseract-ocr-eng tesseract-ocr-script-latn

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
COPY ./*.py /code/
COPY ./.env /code/.env

#
CMD ["python", "foxpile_main.py"]