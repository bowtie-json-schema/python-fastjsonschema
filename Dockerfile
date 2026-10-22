FROM python:3.16.0a1-alpine
WORKDIR /usr/src/myapp
ARG IMPLEMENTATION_VERSION
RUN python3 -m pip install "fastjsonschema${IMPLEMENTATION_VERSION:+==$IMPLEMENTATION_VERSION}"
COPY metaschemas metaschemas
COPY bowtie_fastjsonschema.py .
CMD ["python3", "bowtie_fastjsonschema.py"]
