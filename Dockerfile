FROM nikolaik/python-nodejs:python3.9-nodejs14

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV NODE_ENV=production

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /usr/src/app/vue_components
WORKDIR /usr/src/app/vue_components
COPY ["./vue_components/package.json", "./vue_components/package-lock.json",  "./"]
RUN npm install --global --production

COPY . /usr/src/app/

RUN npm run build

WORKDIR /usr/src/app

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
