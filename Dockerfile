FROM nikolaik/python-nodejs:python3.9-nodejs14

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV NODE_ENV=production

# Install NPM packages using PNPM
RUN npm install -g pnpm
RUN mkdir --parents /usr/src/app/vue_components
WORKDIR /usr/src/app/vue_components
COPY ["./vue_components/package.json", "./vue_components/pnpm-lock.yaml",  "./"]
RUN pnpm install --global --prod

# Install Python packages
WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install --upgrade pip wheel
RUN apt-get update && apt-get -y install libpq-dev gcc build-essential
RUN pip install -r requirements.txt

COPY . /usr/src/app/

# Build vue webpack bundle
RUN pnpm run build

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
