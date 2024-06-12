FROM python:3.6.9

LABEl maintainer "Job Maathuis <j.maathuis@zgt.nl>"

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader stopwords
RUN python -m nltk.downloader punkt

EXPOSE 5555

CMD ["python", "flask_API.py"]