
import asyncio
import aiohttp
from collections import Counter

URL_ENTREGAS = "http://localhost:8004/web/deliveries"
URL_DISPONIBILIDAD = "http://localhost:8004/web/equipments"

TOTAL_ENTREGAS = 30
TOTAL_DISPONIBILIDAD = 5


async def realizar_solicitud(session, url, servicio, numero):
    try:
        async with session.get(url) as response:
            await response.read()
            return servicio, response.status
    except Exception as error:
        print(f"{servicio} {numero}: {error}")
        return servicio, "ERROR"


async def main():
    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        tareas_entregas = [
            realizar_solicitud(
                session, URL_ENTREGAS, "Entregas", i + 1
            )
            for i in range(TOTAL_ENTREGAS)
        ]

        tareas_disponibilidad = [
            realizar_solicitud(
                session, URL_DISPONIBILIDAD,
                "Disponibilidad", i + 1
            )
            for i in range(TOTAL_DISPONIBILIDAD)
        ]

        resultados = await asyncio.gather(
            *tareas_entregas,
            *tareas_disponibilidad
        )

    conteo = {
        "Entregas": Counter(),
        "Disponibilidad": Counter()
    }

    for servicio, estado in resultados:
        conteo[servicio][estado] += 1

    print("\n===== PRUEBA DE AISLAMIENTO BULKHEAD =====")

    for servicio, estados in conteo.items():
        print(f"\n{servicio}:")
        for estado, cantidad in sorted(
            estados.items(), key=lambda x: str(x[0])
        ):
            print(f"  HTTP {estado}: {cantidad}")

    print("\n==========================================")


if __name__ == "__main__":
    asyncio.run(main())
