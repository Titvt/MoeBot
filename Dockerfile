FROM python:3.10

WORKDIR /root

COPY . .

RUN python -m pip install pipx && \
    pipx install nb-cli && \
    pip install -r requirements.txt

ENV PATH="/root/.local/bin:${PATH}"

CMD ["nb", "run"]
