FROM nikolaik/python-nodejs:python3.9-nodejs14

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV NODE_ENV=production

RUN apt-get update && apt-get -y install libpq-dev gcc build-essential

# Install and configure Poetry
RUN pip install "poetry==1.3.2"
RUN poetry config virtualenvs.create false

# Install NPM packages using PNPM
RUN npm install -g pnpm
RUN mkdir --parents /usr/src/app/vue_components
WORKDIR /usr/src/app/vue_components
COPY ["./vue_components/package.json", "./vue_components/pnpm-lock.yaml",  "./"]
RUN pnpm install --prod

# Install Python packages
WORKDIR /usr/src/app
COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY . /usr/src/app/

# Build vue webpack bundle
WORKDIR /usr/src/app/vue_components
RUN pnpm run build

WORKDIR /usr/src/app
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
