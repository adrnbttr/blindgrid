"""Messages français."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    "app.help": (
        "Génère des grilles de loterie à partir d'un tirage cryptographique et "
        "planifie le mois sous un plafond de budget strict. Cet outil ne prédit rien."
    ),
    "generate.help": "Établit le plan du mois : combien dépenser, quels tirages, quels numéros.",
    "config.help": "Consulter et modifier la configuration.",
    "lottery.help": "Gérer les définitions de loteries.",
    "player.help": "Gérer les personnes qui jouent.",
    "version.help": "Affiche la version installée.",
    "config.init.help": "Crée un fichier de configuration à partir de l'exemple fourni.",
    "config.show.help": "Affiche la configuration active.",
    "config.edit.help": "Parcourt les valeurs de configuration une par une.",
    "lottery.list.help": "Affiche toutes les loteries configurées.",
    "lottery.add.help": "Ajoute une loterie, ou remplace celle qui porte le même nom.",
    "player.add.help": "Ajoute une personne qui joue, ou la met à jour si le nom existe déjà.",
    "player.list.help": "Affiche les personnes qui jouent, avec plafond et préférences.",
    "player.remove.help": "Retire une personne. Seule sa configuration disparaît.",
    "option.force.init": "Écraser une configuration existante.",
    "argument.player.name": "Qui retirer.",
    "option.config": "Chemin du fichier de configuration.",
    "option.budget": "Budget à utiliser. Avec des joueurs : NOM=MONTANT, répétable.",
    "option.lottery": "Inclure cette loterie. Répétable. Mode solo uniquement.",
    "option.player": "Limiter le plan à ces personnes. Répétable.",
    "option.month": "Mois à planifier, au format AAAA-MM. Par défaut le mois en cours.",
    "option.force": "Tirer un nouveau plan même si le mois en a déjà un.",
    "option.export": "Écrire l'export Markdown.",
    "option.compact": "Forcer l'affichage compact ou le tableau. Par défaut : selon la largeur.",
    "option.lang": "Langue pour cette exécution.",
    "prompt.budget": "Budget pour ce mois ?",
    "prompt.budget.player": "Budget de {name} ? (vide pour ne pas jouer ce mois-ci)",
    "prompt.lotteries": "Quelles loteries voulez-vous inclure ?",
    "prompt.player.lotteries": "À quelles loteries cette personne joue-t-elle ?",
    "prompt.player.name": "Nom ?",
    "prompt.player.ceiling": "Plafond mensuel strict pour {name} ?",
    "prompt.weight": "Poids pour {label} ?",
    "prompt.ceiling": "Plafond mensuel strict ?",
    "prompt.export": "Exporter le plan vers ?",
    "prompt.filters": "Filtres anti-motifs actifs",
    "prompt.language": "Langue ?",
    "prompt.lottery.label": "Nom ?",
    "prompt.lottery.currency": "Devise ?",
    "prompt.lottery.price": "Prix par grille ?",
    "prompt.lottery.days": "Jours de tirage",
    "prompt.lottery.weight": "Poids ? (part relative, 0 pour désactiver)",
    "prompt.pool.name": "Nom du groupe {number} ?",
    "prompt.pool.count": "Combien de numéros sont tirés ?",
    "prompt.pool.max": "Tirés de 1 à ?",
    "prompt.pool.another": "Ajouter un autre groupe ?",
    "choice.per.grid": "{price} {currency} la grille",
    "choice.per.grid.weight": "{price} {currency} la grille, poids {weight}",
    "plan.title": "Tirages à jouer — {month} {year}",
    "plan.column.date": "Date",
    "plan.column.day": "Jour",
    "plan.column.player": "Joueur",
    "plan.column.lottery": "Loterie",
    "plan.column.numbers": "Numéros",
    "plan.column.cost": "Coût",
    "plan.column.weight": "Poids",
    "plan.column.allocated": "Alloué",
    "plan.column.committed": "Engagé",
    "plan.column.grids": "Grilles",
    "plan.column.unused": "Inutilisé",
    "plan.column.unspent": "Non dépensé",
    "plan.column.budget": "Budget",
    "plan.column.plays": "Joue à",
    "plan.column.ceiling": "Plafond",
    "plan.summary.title": "Répartition du budget",
    "plan.players.title": "Par personne",
    "plan.totals.title": "Totaux",
    "plan.totals.household": "Totaux du foyer",
    "plan.empty": "Aucun tirage ne peut être planifié avec ce budget.",
    "plan.plays.nothing": "rien ce mois-ci",
    "plan.disclaimer": (
        "Les tirages sont des événements indépendants. Ces numéros ne sont pas des "
        "prédictions, et aucune combinaison n'est plus probable qu'une autre."
    ),
    "plan.ceiling": "Plafond mensuel : ",
    "plan.exported": "Exporté vers {path}",
    "plan.already.drawn": (
        "Plan déjà tiré le {date}. Affiché à nouveau — utilisez --force pour en tirer un autre."
    ),
    "plan.replacing": "Remplacement du plan tiré le {date}",
    "plan.replacing.warning": (
        "Retirer jusqu'à ce que les numéros plaisent est précisément le biais que cet "
        "outil supprime."
    ),
    "plan.player.line": "{name} — plafond {ceiling}, joue à {lotteries}",
    "plan.player.nothing": "rien",
    "note.shared": "Tirages partagés",
    "note.shared.body": (
        "{count} tirage(s) sont joués par plusieurs personnes : {listed}. "
        "Partager un tirage ne change rien aux probabilités."
    ),
    "note.no.draw": "aucun tirage restant sur cette période",
    "note.unplayed": (
        "plus que {available} tirage(s) sur la période, "
        "{unplayed} grille(s) finançable(s) non jouée(s)"
    ),
    "note.below.price": (
        "part de {share} inférieure au prix de {price} par grille, ignorée ce mois-ci"
    ),
    "note.disabled": "désactivée (poids nul)",
    "config.file": "Fichier",
    "config.ceiling": "Plafond mensuel",
    "config.export": "Chemin d'export",
    "config.filters": "Filtres",
    "config.lotteries": "Loteries",
    "config.players": "Joueurs",
    "config.language": "Langue",
    "config.plan": "Plan en cours",
    "config.plan.none": "aucun tirage effectué",
    "config.plan.unreadable": "illisible",
    "config.plan.drawn": "{month} {year}, tiré le {date}",
    "config.saved": "{path} enregistré",
    "config.wrote": "{path} créé",
    "config.review": "Vérifiez les prix et les jours de tirage avant de jouer.",
    "config.none": "aucun",
    "player.saved": "Enregistrement de {name} dans {path}",
    "player.removed": "Suppression de {name} dans {path}",
    "player.updating": "Mise à jour de {name}.",
    "player.none": "Aucun joueur configuré — « generate » planifie pour une seule personne.",
    "player.add.hint": "Ajoutez quelqu'un avec « blindgrid player add ».",
    "player.second.hint": (
        "Ajoutez une deuxième personne et « generate » planifiera pour le foyer."
    ),
    "player.weight.explain": (
        "Les poids sont des parts relatives du budget de la personne, pas des nombres de tirages."
    ),
    "player.weight.example": (
        "Des poids égaux répartissent à parts égales ; 0.5 signifie deux fois moins qu'un 1.0."
    ),
    "lottery.saved": "{label} enregistrée dans {path}",
    "error.config.missing": (
        "Aucune configuration trouvée à {path}.\n"
        "Lancez « blindgrid config init » pour en créer une."
    ),
    "error.no.tty": (
        "Cette étape nécessite un terminal interactif. Passez les valeurs en "
        "options, par exemple : blindgrid generate --budget 30 --lottery Loto"
    ),
    "error.prefix": "Erreur : ",
    "error.cancelled": "Annulé.",
    "error.budget.invalid": "{who}{value} n'est pas un montant valide",
    "error.budget.zero": "{who}le budget doit être supérieur à zéro.",
    "error.budget.ceiling": (
        "{who}budget de {amount} supérieur au plafond configuré de {ceiling}. "
        "Modifiez max_monthly_budget dans votre configuration si c'est une décision réfléchie."
    ),
    "error.month": "{value} n'est pas un mois valide. Format attendu AAAA-MM, par exemple 2026-08.",
    "error.lottery.unknown": "Loterie inconnue : {label}. Configurées : {known}",
    "error.player.unknown": "Joueur inconnu : {name}. Configurés : {known}",
    "error.no.lottery": "Aucune loterie avec un poids non nul n'est configurée.",
    "error.none.selected": "Aucune loterie sélectionnée.",
    "error.nobody": "Personne ne joue ce mois-ci.",
    "error.budget.format": (
        "Avec des joueurs configurés, --budget attend NOM=MONTANT, par exemple --budget "
        "'{example}=30'. Reçu {value}."
    ),
    "error.lottery.solo": (
        "--lottery ne vaut qu'en mode solo. Avec des joueurs configurés, les loteries de "
        "chacun viennent de ses propres poids."
    ),
    "error.player.solo": (
        "--player nécessite des joueurs dans votre configuration. "
        "Ajoutez-en un avec « blindgrid player add »."
    ),
    "error.exists": "{path} existe déjà. Utilisez --force pour l'écraser.",
    "error.name.empty": "Un joueur doit avoir un nom.",
    "error.plays.nothing": "Quelqu'un qui ne joue à rien n'a rien à planifier.",
    "error.no.lotteries": "Ajoutez d'abord une loterie avec « blindgrid lottery add ».",
    "error.not.number": "{value} n'est pas un nombre",
    "error.weight.positive": ("Le poids de {label} doit être supérieur à zéro, ou décochez-la."),
    "error.plan.ignored": "Plan enregistré ignoré : {reason}",
    "error.plan.unsaved": "Impossible d'enregistrer ce plan, il ne sera pas mémorisé : {reason}",
    "error.language": "Langue inconnue : {value}. Disponibles : {known}",
    "month.1": "janvier",
    "month.2": "février",
    "month.3": "mars",
    "month.4": "avril",
    "month.5": "mai",
    "month.6": "juin",
    "month.7": "juillet",
    "month.8": "août",
    "month.9": "septembre",
    "month.10": "octobre",
    "month.11": "novembre",
    "month.12": "décembre",
    # Abbreviations as each language actually writes them: German uses two
    # letters, not a truncation of the full name.
    "weekday.short.0": "lun",
    "weekday.short.1": "mar",
    "weekday.short.2": "mer",
    "weekday.short.3": "jeu",
    "weekday.short.4": "ven",
    "weekday.short.5": "sam",
    "weekday.short.6": "dim",
    "weekday.0": "lundi",
    "weekday.1": "mardi",
    "weekday.2": "mercredi",
    "weekday.3": "jeudi",
    "weekday.4": "vendredi",
    "weekday.5": "samedi",
    "weekday.6": "dimanche",
}
