FROM python:3.7

RUN apt-get update

RUN apt-get install libgeos++-dev libproj-dev -y

RUN mkdir -p /app

COPY . /app/

WORKDIR /app

RUN pip --disable-pip-version-check install -r requirements.txt

RUN pip --disable-pip-version-check install pykdtree scipy

# From: https://stackoverflow.com/questions/60111684/geometry-must-be-a-point-or-linestring-error-using-cartopy

RUN pip uninstall shapely -y

RUN pip install shapely --no-binary shapely

RUN chmod +x *.py *.sh

RUN mkdir -p /app/output

VOLUME ["/app/output"]

CMD ["./docker-execution.sh"]
