FROM python:latest

WORKDIR /root

ENV PATH="/root/.local/bin:${PATH}"

COPY requirements.txt .

RUN python -m pip install pipx && \
    pipx install nb-cli && \
    pip install -r requirements.txt

COPY . .

CMD ["nb", "run"]
