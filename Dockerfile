FROM node:24-bookworm-slim AS frontend
WORKDIR /work
COPY frontend/package*.json frontend/
RUN npm --prefix frontend ci --ignore-scripts
COPY frontend frontend
COPY LICENSE NOTICE.md ./
COPY src/boston_housing/artifacts src/boston_housing/artifacts
RUN npm --prefix frontend run build

FROM python:3.13-slim AS package
WORKDIR /work
COPY . .
COPY --from=frontend /work/frontend/dist frontend/dist
RUN python scripts/package_site.py && pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.13-slim
RUN useradd --create-home --uid 10001 researcher
COPY --from=package /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels boston-housing-workbench && rm -rf /wheels
USER researcher
WORKDIR /home/researcher
EXPOSE 8000
CMD ["uvicorn", "boston_housing.web:app", "--host", "0.0.0.0", "--port", "8000"]