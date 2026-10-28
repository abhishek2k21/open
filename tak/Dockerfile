FROM apify/actor-python:3.12

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && python3 --version && pip --version && pip freeze

COPY . ./
RUN python3 -m compileall -q src/

CMD ["python3", "-m", "src.main"]
