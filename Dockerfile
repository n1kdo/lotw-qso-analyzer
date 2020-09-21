FROM python:3.7

RUN mkdir -p /app

COPY *.py *.iml requirements.txt /app/

WORKDIR /app

RUN apt-get update

RUN apt-get install libgeos++-dev libproj-dev -y

RUN pip --disable-pip-version-check install -r requirements.txt

RUN pip --disable-pip-version-check install pykdtree scipy

# From: https://stackoverflow.com/questions/60111684/geometry-must-be-a-point-or-linestring-error-using-cartopy

RUN pip uninstall shapely -y

RUN pip install shapely --no-binary shapely

RUN chmod +x *.py
