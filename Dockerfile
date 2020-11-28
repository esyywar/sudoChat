FROM python:3.8.6-buster

ADD my_script.py /

RUN pip install pystrich

CMD [ "python", "./my_script.py" ]