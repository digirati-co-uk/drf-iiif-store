FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y nginx gdal-bin git

# Set up Nginx
RUN addgroup --system nginx
RUN adduser --system nginx
RUN usermod -a -G nginx nginx
RUN mkdir -p /run/nginx

RUN mkdir -p /var/log/nginx && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stdout /var/log/nginx/error.log && \
    mkdir /app && \
    mkdir /app_static
 
COPY ./example_project/requirements.txt /app
COPY ./example_project/nginx.conf /etc/nginx/nginx.conf

WORKDIR /app
RUN pip3 install -r requirements.txt

COPY ./example_project /app
COPY ./iiif_store /app/iiif_store

COPY ./example_project/entrypoint /entrypoint

RUN sed -i 's/\r$//g' /entrypoint && \
    chmod +x /entrypoint

CMD /entrypoint
