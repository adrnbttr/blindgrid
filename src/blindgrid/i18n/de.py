"""Deutsche Meldungen."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    "app.help": (
        "Erzeugt Lottoscheine aus kryptografischem Zufall und plant den Monat "
        "innerhalb einer festen Budgetgrenze. Dieses Werkzeug sagt nichts vorher."
    ),
    "generate.help": "Erstellt den Monatsplan: wie viel, welche Ziehungen, welche Zahlen.",
    "config.help": "Konfiguration ansehen und bearbeiten.",
    "lottery.help": "Lotterie-Definitionen verwalten.",
    "player.help": "Die Personen verwalten, die spielen.",
    "version.help": "Zeigt die installierte Version.",
    "option.config": "Pfad zur Konfigurationsdatei.",
    "option.budget": "Zu verwendendes Budget. Mit Spielern: NAME=BETRAG, wiederholbar.",
    "option.lottery": "Diese Lotterie einbeziehen. Wiederholbar. Nur im Einzelmodus.",
    "option.player": "Den Plan auf diese Personen beschränken. Wiederholbar.",
    "option.month": "Zu planender Monat, als JJJJ-MM. Standard ist der laufende Monat.",
    "option.force": "Neu ziehen, auch wenn für diesen Monat schon ein Plan besteht.",
    "option.export": "Den Markdown-Export schreiben.",
    "option.compact": "Schmale Ansicht oder Tabelle erzwingen. Standard: nach Breite.",
    "option.lang": "Sprache für diesen Lauf.",
    "prompt.budget": "Budget für diesen Monat?",
    "prompt.budget.player": "Budget für {name}? (leer lassen, um auszusetzen)",
    "prompt.lotteries": "Welche Lotterien sollen dabei sein?",
    "prompt.player.lotteries": "Welche Lotterien spielt diese Person?",
    "prompt.player.name": "Name?",
    "prompt.player.ceiling": "Feste Monatsgrenze für {name}?",
    "prompt.weight": "Gewicht für {label}?",
    "prompt.ceiling": "Feste Monatsgrenze?",
    "prompt.export": "Plan exportieren nach?",
    "prompt.filters": "Aktive Muster-Filter",
    "prompt.language": "Sprache?",
    "prompt.lottery.label": "Bezeichnung?",
    "prompt.lottery.currency": "Währung?",
    "prompt.lottery.price": "Preis pro Tipp?",
    "prompt.lottery.days": "Ziehungstage",
    "prompt.lottery.weight": "Gewicht? (relativer Anteil, 0 deaktiviert)",
    "prompt.pool.name": "Name der {number}. Gruppe?",
    "prompt.pool.count": "Wie viele Zahlen werden gezogen?",
    "prompt.pool.max": "Höchste Zahl?",
    "prompt.pool.another": "Weitere Gruppe hinzufügen?",
    "choice.per.grid": "{price} {currency} pro Tipp",
    "choice.per.grid.weight": "{price} {currency} pro Tipp, Gewicht {weight}",
    "plan.title": "Zu spielende Ziehungen — {month} {year}",
    "plan.column.date": "Datum",
    "plan.column.day": "Tag",
    "plan.column.player": "Spieler",
    "plan.column.lottery": "Lotterie",
    "plan.column.numbers": "Zahlen",
    "plan.column.cost": "Kosten",
    "plan.column.weight": "Gewicht",
    "plan.column.allocated": "Zugeteilt",
    "plan.column.committed": "Eingesetzt",
    "plan.column.grids": "Tipps",
    "plan.column.unused": "Ungenutzt",
    "plan.column.unspent": "Übrig",
    "plan.column.budget": "Budget",
    "plan.column.plays": "Spielt",
    "plan.column.ceiling": "Grenze",
    "plan.summary.title": "Budgetaufteilung",
    "plan.players.title": "Pro Person",
    "plan.totals.title": "Summen",
    "plan.totals.household": "Haushaltssummen",
    "plan.empty": "Mit diesem Budget lässt sich keine Ziehung planen.",
    "plan.plays.nothing": "diesen Monat nichts",
    "plan.disclaimer": (
        "Ziehungen sind unabhängige Ereignisse. Diese Zahlen sind keine Vorhersagen, "
        "und keine Kombination ist wahrscheinlicher als eine andere."
    ),
    "plan.ceiling": "Monatsgrenze: ",
    "plan.exported": "Exportiert nach {path}",
    "plan.already.drawn": (
        "Plan wurde am {date} bereits gezogen. Wird erneut angezeigt — mit --force neu ziehen."
    ),
    "plan.replacing": "Ersetze den am {date} gezogenen Plan",
    "plan.replacing.warning": (
        "Immer wieder neu zu ziehen, bis die Zahlen gefallen, ist genau jene "
        "Verzerrung, die dieses Werkzeug beseitigt."
    ),
    "plan.player.line": "{name} — Grenze {ceiling}, spielt {lotteries}",
    "plan.player.nothing": "nichts",
    "note.shared": "Geteilte Ziehungen",
    "note.shared.body": (
        "{count} Ziehung(en) werden von mehreren Personen gespielt: {listed}. "
        "Eine Ziehung zu teilen ändert nichts an den Chancen."
    ),
    "note.no.draw": "keine Ziehung mehr in diesem Zeitraum",
    "note.unplayed": (
        "nur noch {available} Ziehung(en) im Zeitraum, {unplayed} bezahlbare(r) Tipp(s) ungespielt"
    ),
    "note.below.price": (
        "Anteil von {share} liegt unter dem Preis von {price} pro Tipp, diesen Monat übersprungen"
    ),
    "note.disabled": "deaktiviert (Gewicht ist 0)",
    "config.file": "Datei",
    "config.ceiling": "Monatsgrenze",
    "config.export": "Exportpfad",
    "config.filters": "Filter",
    "config.lotteries": "Lotterien",
    "config.players": "Spieler",
    "config.language": "Sprache",
    "config.plan": "Aktueller Plan",
    "config.plan.none": "noch keiner gezogen",
    "config.plan.unreadable": "unlesbar",
    "config.plan.drawn": "{month} {year}, gezogen am {date}",
    "config.saved": "{path} gespeichert",
    "config.wrote": "{path} angelegt",
    "config.review": "Prüfen Sie Preise und Ziehungstage, bevor Sie spielen.",
    "config.none": "keine",
    "player.saved": "{name} in {path} gespeichert",
    "player.removed": "{name} aus {path} entfernt",
    "player.updating": "{name} wird aktualisiert.",
    "player.none": "Keine Spieler konfiguriert — „generate“ plant für eine Person.",
    "player.add.hint": "Fügen Sie jemanden mit „blindgrid player add“ hinzu.",
    "player.second.hint": (
        "Fügen Sie eine zweite Person hinzu, dann plant „generate“ für den Haushalt."
    ),
    "player.weight.explain": (
        "Gewichte sind relative Anteile am Budget dieser Person, keine Anzahl von Ziehungen."
    ),
    "player.weight.example": (
        "Gleiche Gewichte teilen gleichmäßig; 0.5 bedeutet halb so viel wie 1.0."
    ),
    "lottery.saved": "{label} in {path} gespeichert",
    "error.config.missing": (
        "Keine Konfiguration unter {path} gefunden.\nLegen Sie mit „blindgrid config init“ eine an."
    ),
    "error.no.tty": (
        "Dieser Schritt braucht ein interaktives Terminal. Übergeben Sie die "
        "Werte als Optionen, etwa: blindgrid generate --budget 30 --lottery Loto"
    ),
    "error.prefix": "Fehler: ",
    "error.cancelled": "Abgebrochen.",
    "error.budget.invalid": "{who}{value} ist kein gültiger Betrag",
    "error.budget.zero": "{who}das Budget muss größer als null sein.",
    "error.budget.ceiling": (
        "{who}Budget von {amount} übersteigt die konfigurierte Grenze von {ceiling}. "
        "Ändern Sie max_monthly_budget, wenn das eine bewusste Entscheidung ist."
    ),
    "error.month": "{value} ist kein gültiger Monat. Erwartet wird JJJJ-MM, etwa 2026-08.",
    "error.lottery.unknown": "Unbekannte Lotterie: {label}. Konfiguriert: {known}",
    "error.player.unknown": "Unbekannter Spieler: {name}. Konfiguriert: {known}",
    "error.no.lottery": "Es ist keine Lotterie mit einem Gewicht ungleich null konfiguriert.",
    "error.none.selected": "Keine Lotterie ausgewählt.",
    "error.nobody": "Diesen Monat spielt niemand.",
    "error.budget.format": (
        "Mit konfigurierten Spielern erwartet --budget NAME=BETRAG, etwa --budget "
        "'{example}=30'. Erhalten: {value}."
    ),
    "error.lottery.solo": (
        "--lottery gilt nur im Einzelmodus. Mit konfigurierten Spielern ergeben sich die "
        "Lotterien jeder Person aus ihren eigenen Gewichten."
    ),
    "error.player.solo": (
        "--player benötigt Spieler in der Konfiguration. "
        "Fügen Sie einen mit „blindgrid player add“ hinzu."
    ),
    "error.exists": "{path} existiert bereits. Überschreiben Sie sie mit --force.",
    "error.name.empty": "Ein Spieler braucht einen Namen.",
    "error.plays.nothing": "Wer nichts spielt, hat nichts zu planen.",
    "error.no.lotteries": "Fügen Sie zuerst eine Lotterie mit „blindgrid lottery add“ hinzu.",
    "error.not.number": "{value} ist keine Zahl",
    "error.weight.positive": (
        "Das Gewicht für {label} muss größer als null sein, sonst wählen Sie sie ab."
    ),
    "error.plan.ignored": "Gespeicherter Plan wird ignoriert: {reason}",
    "error.plan.unsaved": (
        "Dieser Plan konnte nicht gespeichert werden und wird vergessen: {reason}"
    ),
    "error.language": "Unbekannte Sprache: {value}. Verfügbar: {known}",
    "month.1": "Januar",
    "month.2": "Februar",
    "month.3": "März",
    "month.4": "April",
    "month.5": "Mai",
    "month.6": "Juni",
    "month.7": "Juli",
    "month.8": "August",
    "month.9": "September",
    "month.10": "Oktober",
    "month.11": "November",
    "month.12": "Dezember",
    "weekday.0": "Montag",
    "weekday.1": "Dienstag",
    "weekday.2": "Mittwoch",
    "weekday.3": "Donnerstag",
    "weekday.4": "Freitag",
    "weekday.5": "Samstag",
    "weekday.6": "Sonntag",
}
