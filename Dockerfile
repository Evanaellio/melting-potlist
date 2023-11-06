FROM node:lts as vite_build

ENV NODE_ENV=production
ENV NODE_OPTIONS=--openssl-legacy-provider

# Install NPM packages using PNPM
RUN npm install -g pnpm
WORKDIR /build/vue_components
COPY ["./vue_components/package.json", "./vue_components/pnpm-lock.yaml",  "./"]
RUN pnpm install --prod

# Build using vite
COPY ./vue_components ./
RUN pnpm run build


FROM python:3.12 as django_app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install and configure Poetry
RUN pip install "poetry==1.7.0"
RUN poetry config virtualenvs.create false

# Install Python packages
WORKDIR /usr/src/app
COPY ./pyproject.toml ./poetry.lock ./
RUN poetry install --only main --no-root --no-interaction --no-ansi

COPY . ./
COPY --from=vite_build /build/vue_components/dist /usr/src/app/vue_components/dist
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
