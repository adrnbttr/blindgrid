"""Mensajes en español."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    "app.help": (
        "Genera combinaciones de lotería a partir de aleatoriedad criptográfica y "
        "planifica el mes bajo un límite de presupuesto estricto. Esta herramienta "
        "no predice nada."
    ),
    "generate.help": "Crea el plan del mes: cuánto gastar, qué sorteos, qué números.",
    "config.help": "Consultar y editar la configuración.",
    "lottery.help": "Gestionar las definiciones de loterías.",
    "player.help": "Gestionar a las personas que juegan.",
    "version.help": "Muestra la versión instalada.",
    "config.init.help": "Crea un archivo de configuración a partir del ejemplo incluido.",
    "config.show.help": "Muestra la configuración activa.",
    "config.edit.help": "Recorre los valores de configuración uno por uno.",
    "lottery.list.help": "Muestra todas las loterías configuradas.",
    "lottery.add.help": "Añade una lotería, o sustituye la que tenga el mismo nombre.",
    "player.add.help": "Añade a alguien que juega, o lo actualiza si el nombre ya existe.",
    "player.list.help": "Muestra quién juega, con su límite y sus preferencias.",
    "player.remove.help": "Elimina a alguien. Solo desaparece su configuración.",
    "option.force.init": "Sobrescribir una configuración existente.",
    "argument.player.name": "A quién eliminar.",
    "option.config": "Ruta del archivo de configuración.",
    "option.budget": "Presupuesto a usar. Con jugadores: NOMBRE=IMPORTE, repetible.",
    "option.lottery": "Incluir esta lotería. Repetible. Solo en modo individual.",
    "option.player": "Limitar el plan a estas personas. Repetible.",
    "option.month": "Mes a planificar, en formato AAAA-MM. Por defecto, el mes actual.",
    "option.force": "Sortear un plan nuevo aunque este mes ya tenga uno.",
    "option.export": "Escribir la exportación en Markdown.",
    "option.compact": "Forzar la vista compacta o la tabla. Por defecto: según el ancho.",
    "option.lang": "Idioma para esta ejecución.",
    "prompt.budget": "¿Presupuesto para este mes?",
    "prompt.budget.player": "¿Presupuesto de {name}? (vacío para no jugar este mes)",
    "prompt.lotteries": "¿Qué loterías quieres incluir?",
    "prompt.player.lotteries": "¿A qué loterías juega esta persona?",
    "prompt.player.name": "¿Nombre?",
    "prompt.player.ceiling": "¿Límite mensual estricto para {name}?",
    "prompt.weight": "¿Peso para {label}?",
    "prompt.ceiling": "¿Límite mensual estricto?",
    "prompt.export": "¿Dónde exportar el plan?",
    "prompt.filters": "Filtros anti-patrón activos",
    "prompt.language": "¿Idioma?",
    "prompt.lottery.label": "¿Nombre?",
    "prompt.lottery.currency": "¿Moneda?",
    "prompt.lottery.price": "¿Precio por apuesta?",
    "prompt.lottery.days": "Días de sorteo",
    "prompt.lottery.weight": "¿Peso? (parte relativa, 0 lo desactiva)",
    "prompt.pool.name": "¿Nombre del grupo {number}?",
    "prompt.pool.count": "¿Cuántos números se sortean?",
    "prompt.pool.max": "¿Número más alto?",
    "prompt.pool.another": "¿Añadir otro grupo?",
    "choice.per.grid": "{price} {currency} por apuesta",
    "choice.per.grid.weight": "{price} {currency} por apuesta, peso {weight}",
    "plan.title": "Sorteos a jugar — {month} {year}",
    "plan.column.date": "Fecha",
    "plan.column.day": "Día",
    "plan.column.player": "Jugador",
    "plan.column.lottery": "Lotería",
    "plan.column.numbers": "Números",
    "plan.column.cost": "Coste",
    "plan.column.weight": "Peso",
    "plan.column.allocated": "Asignado",
    "plan.column.committed": "Comprometido",
    "plan.column.grids": "Apuestas",
    "plan.column.unused": "Sin usar",
    "plan.column.unspent": "Sin gastar",
    "plan.column.budget": "Presupuesto",
    "plan.column.plays": "Juega a",
    "plan.column.ceiling": "Límite",
    "plan.summary.title": "Reparto del presupuesto",
    "plan.players.title": "Por persona",
    "plan.totals.title": "Totales",
    "plan.totals.household": "Totales del hogar",
    "plan.empty": "No se puede planificar ningún sorteo con este presupuesto.",
    "plan.plays.nothing": "nada este mes",
    "plan.disclaimer": (
        "Los sorteos son sucesos independientes. Estos números no son predicciones, "
        "y ninguna combinación es más probable que otra."
    ),
    "plan.ceiling": "Límite mensual: ",
    "plan.exported": "Exportado a {path}",
    "plan.already.drawn": (
        "El plan ya se sorteó el {date}. Se muestra de nuevo — usa --force para sortear otro."
    ),
    "plan.replacing": "Sustituyendo el plan sorteado el {date}",
    "plan.replacing.warning": (
        "Volver a sortear hasta que los números gusten es justo el sesgo que esta "
        "herramienta elimina."
    ),
    "plan.player.line": "{name} — límite {ceiling}, juega a {lotteries}",
    "plan.player.nothing": "nada",
    "note.shared": "Sorteos compartidos",
    "note.shared.body": (
        "{count} sorteo(s) los juega más de una persona: {listed}. "
        "Compartir un sorteo no cambia las probabilidades."
    ),
    "note.no.draw": "no queda ningún sorteo en este periodo",
    "note.unplayed": (
        "solo quedan {available} sorteo(s) en el periodo, "
        "{unplayed} apuesta(s) asequible(s) sin jugar"
    ),
    "note.below.price": (
        "la parte de {share} no llega al precio de {price} por apuesta, se omite este mes"
    ),
    "note.disabled": "desactivada (peso cero)",
    "config.file": "Archivo",
    "config.ceiling": "Límite mensual",
    "config.export": "Ruta de exportación",
    "config.filters": "Filtros",
    "config.lotteries": "Loterías",
    "config.players": "Jugadores",
    "config.language": "Idioma",
    "config.plan": "Plan actual",
    "config.plan.none": "ninguno todavía",
    "config.plan.unreadable": "ilegible",
    "config.plan.drawn": "{month} {year}, sorteado el {date}",
    "config.saved": "{path} guardado",
    "config.wrote": "{path} creado",
    "config.review": "Revisa los precios y los días de sorteo antes de jugar.",
    "config.none": "ninguno",
    "player.saved": "{name} se ha guardado en {path}",
    "player.removed": "{name} se ha eliminado de {path}",
    "player.updating": "Actualizando a {name}.",
    "player.none": "No hay jugadores configurados — «generate» planifica para una sola persona.",
    "player.add.hint": "Añade a alguien con «blindgrid player add».",
    "player.second.hint": "Añade una segunda persona y «generate» planificará para el hogar.",
    "player.weight.explain": (
        "Los pesos son partes relativas del presupuesto de esa persona, no números de sorteos."
    ),
    "player.weight.example": (
        "Pesos iguales lo reparten por igual; 0.5 significa la mitad que un 1.0."
    ),
    "lottery.saved": "{label} guardada en {path}",
    "error.config.missing": (
        "No se encontró ninguna configuración en {path}.\n"
        "Ejecuta «blindgrid config init» para crear una."
    ),
    "error.no.tty": (
        "Este paso necesita un terminal interactivo. Pasa los valores como "
        "opciones, por ejemplo: blindgrid generate --budget 30 --lottery Loto"
    ),
    "error.prefix": "Error: ",
    "error.cancelled": "Cancelado.",
    "error.budget.invalid": "{who}{value} no es un importe válido",
    "error.budget.zero": "{who}el presupuesto debe ser mayor que cero.",
    "error.budget.ceiling": (
        "{who}presupuesto de {amount} superior al límite configurado de {ceiling}. "
        "Cambia max_monthly_budget en tu configuración si es una decisión meditada."
    ),
    "error.month": "{value} no es un mes válido. Se espera AAAA-MM, por ejemplo 2026-08.",
    "error.lottery.unknown": "Lotería desconocida: {label}. Configuradas: {known}",
    "error.player.unknown": "Jugador desconocido: {name}. Configurados: {known}",
    "error.no.lottery": "No hay ninguna lotería configurada con peso distinto de cero.",
    "error.none.selected": "No se ha seleccionado ninguna lotería.",
    "error.nobody": "Nadie juega este mes.",
    "error.budget.format": (
        "Con jugadores configurados, --budget espera NOMBRE=IMPORTE, por ejemplo --budget "
        "'{example}=30'. Se recibió {value}."
    ),
    "error.lottery.solo": (
        "--lottery solo vale en modo individual. Con jugadores configurados, las loterías "
        "de cada persona salen de sus propios pesos."
    ),
    "error.player.solo": (
        "--player necesita jugadores en tu configuración. Añade uno con «blindgrid player add»."
    ),
    "error.exists": "{path} ya existe. Usa --force para sobrescribirlo.",
    "error.name.empty": "Un jugador necesita un nombre.",
    "error.plays.nothing": "Quien no juega a nada no tiene nada que planificar.",
    "error.no.lotteries": "Añade primero una lotería con «blindgrid lottery add».",
    "error.not.number": "{value} no es un número",
    "error.weight.positive": ("El peso de {label} debe ser mayor que cero, o desmárcala."),
    "error.plan.ignored": "Se ignora el plan guardado: {reason}",
    "error.plan.unsaved": "No se pudo guardar este plan, no se recordará: {reason}",
    "error.language": "Idioma desconocido: {value}. Disponibles: {known}",
    "month.1": "enero",
    "month.2": "febrero",
    "month.3": "marzo",
    "month.4": "abril",
    "month.5": "mayo",
    "month.6": "junio",
    "month.7": "julio",
    "month.8": "agosto",
    "month.9": "septiembre",
    "month.10": "octubre",
    "month.11": "noviembre",
    "month.12": "diciembre",
    "weekday.0": "lunes",
    "weekday.1": "martes",
    "weekday.2": "miércoles",
    "weekday.3": "jueves",
    "weekday.4": "viernes",
    "weekday.5": "sábado",
    "weekday.6": "domingo",
}
