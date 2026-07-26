FROM python:3.15.0b4-alpine
WORKDIR /usr/src/myapp
ARG IMPLEMENTATION_VERSION
RUN python3 -m pip install "fastjsonschema${IMPLEMENTATION_VERSION:+==$IMPLEMENTATION_VERSION}"
COPY bowtie_fastjsonschema.py .
CMD ["python3", "bowtie_fastjsonschema.py"]
