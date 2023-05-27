FROM python:3.10
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip3 install -r requirements.txt
COPY . .
COPY *.py ./
ENV PORT=8000
EXPOSE ${PORT}
ENV GOOGLE_APPLICATION_CREDENTIALS='./hw8-paceym-9d2839f50c3c.json'
CMD [ "python", "main.py" ]
