FROM python:3.9
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN pip install waitress
WORKDIR site/
COPY . ./
CMD ["waitress-serve", "--port=5000", "main:app"]