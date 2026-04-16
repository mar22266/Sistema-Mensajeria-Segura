# Sistema-Mensajeria-Segura

para correr el proyecto la parte del modulo 1, 2 y 3

```bash
 docker compose up --build
```

unicamente con ese comando y se dirige uno al url

http://localhost:8000/docs#/

ya ahi se pueden probar todos los endpoints. se debe tener el docker levantado para conectarse la base de datos y hacer las pruebas con los comandos de abajo

para conectarse a la base de datos:

```bash
docker exec -it sistema_mensajeria_db psql -U postgres -d sistema_mensajeria_segura
```

para correr los tests y verificarlos:

```bash
docker exec -it sistema_mensajeria_api pytest -v
```
