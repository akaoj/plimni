FROM alpine:3.9

RUN apk add --no-cache python3=3.6.8-r2
RUN python3.6 -m pip install -U pip

RUN mkdir /code
WORKDIR /code

COPY requirements.prod.txt ./requirements.prod.txt
RUN pip3 install --user --no-cache-dir -r ./requirements.prod.txt

COPY plimni ./plimni

CMD ["python3", "-m", "plimni"]
