# Grupo-20-Forma-M-Arriendo-de-equipos

# Arriendo de Equipos

Sistema de arriendo de equipos desarrollado mediante una arquitectura de microservicios, utilizando Python, FastAPI, Docker Compose y bases de datos PostgreSQL.

## Ejecución del proyecto

El sistema se encuentra completamente dockerizado y puede levantarse desde la raíz del repositorio mediante Docker Compose.

Antes de iniciar los servicios, se debe crear un archivo `.env` en la raíz del proyecto y definir la variable utilizada para la autenticación del API Gateway:

```env
GATEWAY_API_TOKEN=dev-token
```

Posteriormente, desde la raíz del repositorio, ejecutar:

```bash
docker compose up --build -d
```

Este comando construye y levanta los contenedores correspondientes al API Gateway, BFF Web, microservicios de Disponibilidad, Pagos y Entregas, Orquestador de Saga y sus respectivas bases de datos PostgreSQL.

Para comprobar que los contenedores se encuentran activos, se puede ejecutar:

```bash
docker compose ps
```

## Acceso al sistema

Una vez iniciados los contenedores, el sistema queda accesible a través del API Gateway:

- **API Gateway:** http://localhost:8000
- **Estado del Gateway:** http://localhost:8000/health
- **Dashboard:** http://localhost:8000/web/dashboard
- **Documentación de la API:** http://localhost:8000/docs

Para utilizar los endpoints protegidos se debe incluir el token configurado en el archivo `.env` mediante el encabezado HTTP `Authorization: Bearer`, seguido de la API Key correspondiente.

## Detención del sistema

Para detener los contenedores, ejecutar desde la raíz del repositorio:

```bash
docker compose down
```

Los datos de las bases de datos se almacenan en volúmenes independientes de Docker, por lo que se mantienen al detener y volver a levantar los contenedores, siempre que no se eliminen dichos volúmenes.