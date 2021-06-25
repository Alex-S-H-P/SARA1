from typing import Union

print("-------------------")
import pickle
import re  # for splits
from math import *
import numpy as np
import os
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import time
from dateutil.relativedelta import relativedelta

thx = "de rien"
last_ask = ''
## initialisation
try:
    a = loaded
except NameError:
    loaded = False
if not loaded:
    folder = os.getcwd()
    print('starting to load...')
    synonymes = pickle.load(open(folder + "/language ressources/syn_dict", 'rb'))
    # synonymes ressemble à {mot1:{syn11:score11,syn12:score12...},mot2:{syn21:score21,syn22:score22...}...}
    print(".")
    conjugues = pickle.load(open(folder + "/language ressources/vb_extraire", 'rb'))
    # conjugues ressemble à [[inf1,conj11,conj12...],[inf2,conj21;conj22...],...]
    print("..")
    prenoms = set(pickle.load(open(folder + '/language ressources/prenom', 'rb')))
    # prenoms   ressemble à [prenom1,prenom2,prenom3...]
    global_vars = pickle.load(open(folder + '/global_vars.sara', 'rb'))
    discussion_records = pickle.load((open(folder + '/training_log/records.trn', 'rb')))
    print("...")
    print("done")
    choix = {}
    loaded = True

asking = False
forest = []
## - BRAIN (Binary Reducted Algorithmic Inquieries Network)
sigm = lambda z: 1 / (1 + exp(-z))
asked_memory = []


def avg(iterable):
    return sum(iterable) / len(iterable)


def scramble(t, distance):
    T = t.lower().split()
    n = len(T)
    D = distance
    while distance > 0:
        # score de cette modification
        modif = ((np.random.random()) ** 1 / 10) * D
        mot = T[(i := np.random.randint(0, n - 1))]
        if mot in synonymes and not mot in prenoms:
            L: list[str] = [mot2 for mot2 in synonymes[mot] if synonymes[mot][mot2] <= modif]
            if (p := len(L)) > 0:
                # choosing the best replacing word
                T[i] = choice = L[0] if p == 1 else L[np.random.randint(0, p - 1)]
                distance -= synonymes[mot][choice]
    rep = "".join([mot.capitalize() + " " if "." in T[i - 1] else mot + " " for i, mot in enumerate(T)])
    return rep[:-1]


def say(t, flex: float = 0., hover=None):
    """Affiche le texte t avec un écart permis de /flex/"""
    try:
        if flex > 0:
            t = scramble(t, flex)
        n = len(t)
        label = Label(WIN, text="", bg='PaleGreen')
        if hover is not None:
            CreateToolTip(label, text=str(hover))
        label.pack(anchor='nw')
        for i in range(n):
            label.config(text=t[:i + 1])
            fen.update()
    except Exception:
        print(t)


def ask(t: str, hover=None) -> Union[str, None]:
    T_FIELD.config(state='normal')
    global asking
    T_FIELD.config(bg="lavender")
    if asking:
        DEMAND.set("INTERRUPT")
        T_FIELD.config(bg="linen")
        return None
    asking = True
    say(t, hover=hover)
    SAY.waitvar(DEMAND)
    asking = False
    T_FIELD.config(bg="linen")
    return DEMAND.get()


def merge_dict(dict1: dict, dict2: dict, priorite=1) -> dict:
    """Merges two dictionaries"""
    return dict1.update(dict2) if priorite == 2 else merge_dict(dict2, dict1, 2)


def SARA_input():
    global DEMAND
    global asking
    T_FIELD.config(state="disabled")
    if IMMEDIATE.get() == "INTERRUPT":
        asking = False
        DEMAND.set("INTERRUPT")
        L = Label(WIN, text=IMMEDIATE.get(), bg='linen', fg='red')
        L.pack(anchor='n')
        CreateToolTip(L, text="Interruption des procédés de demande")
        IMMEDIATE.set("")
        T_FIELD.config(state="normal")
        raise Exception(" <DEMANDE INTERROMPUE> ")
    DEMAND.set(IMMEDIATE.get())
    Label(WIN, text=IMMEDIATE.get(), bg='linen', fg='maroon').pack(anchor='ne')
    IMMEDIATE.set('')
    while len(WIN.children) > 20:
        WIN.children[list(WIN.children.keys())[2]].destroy()
    if not asking:
        solve()
    T_FIELD.config(state="normal")


def record(question, answer_given) -> bool:
    """Enregistre la question dans les records.
    Returns true if the interraction was recorded"""
    global discussion_records
    answer = answer_given.store()
    D = {"question": question, "answer": answer}
    if any(all(entry[item] == D[item] for item in ["question", "answer"]) for entry in discussion_records):
        say("This exchange has not been recorded due to presence of a similar one in memory")
        return False
    discussion_records.append({"question": question, "answer": answer, "rectified": False})
    return True


def rectify(question, answer):
    """Corrige une mauvaise activation"""
    global discussion_records
    if isinstance(question, str):
        question = question.split()
    for i, entry in enumerate(discussion_records):
        if entry["question"] == question:
            record[i]["answer"] = answer.store() if answer.__class__.__name__ == "action" else answer.copy()
            return
    say("Aucune entrée n'as été trouvée correspondant à cette rectification.")


def add_training(question: str, answer: str):
    """ajoute un couple question/réponse à l'entrainement!
    La réponse ne doit pas être stockée"""
    address = folder + '/training_log/'

    def add_to_file(_question: str, _answer: str, _address: str) -> dict:
        file = open(_address, "rb")
        file_size = os.path.getsize(_address)
        # print("{} has a file_size of {}".format(address, file_size))
        ## récupérer la base
        if file_size == 0:  # si le fichier est vide
            say("Le fichier à l'adresse {} est vide".format(_address))
            if not positif(ask("Reremplir ce fichier ?")):
                raise Exception("Empty file {}".format(_address))
            _base = {}
        else:
            _base = pickle.load(file)
        ## ajouter à celle-ci
        if _question in _base:
            say("Cette requète à déjà été mémorisée",
                hover="En cas de réception d'un message d'erreur, les deux coexisteront")
            if positif(ask("Voir l'action?")):
                say(str(_base[_question]))
        file.close()
        _base[_question] = _answer.store()
        ## sauvegarder
        pickle.dump(_base, open(_address, 'wb'))
        return _base

    try:
        name = "main.trn"
        add_to_file(question, answer, address + name)
    except FileNotFoundError:
        say("An error occured. Trying again with backup file")
        name = 'bcp.trn'
        base = add_to_file(question, answer, address + name)
    pickle.dump(base, open(address + name, 'wb'))


def solve(detail=True, command=None):
    """
    si detail == False, alors solve passe en mode apprentissage. Les données seront mémorisées, et permettront ainsi un meilleur accés dans le futur.
    """

    def cell_norm(cell, location=False):
        """returns the norm of the cell given the /command/"""
        dist_min, _mot = 2 ** 20, '_____'
        ## blank state
        if cell["_dem"] == ["<blank>"]:
            return dist_min, _mot if location else dist_min
        ## normal
        for dem in cell['_dem']:
            # print(cell["_nam"],dem)
            global last_cell
            last_cell = cell
            # print(cell)
            activateur = dem.split()
            n = len(activateur)
            if n == 0:
                if 3 < dist_min:
                    dist_min, _mot = 3, ''
                continue
            for i in range(len(command) + 1 - n):
                distance = sum(distance_mot(activateur[k], command[i + k]) for k in range(n))
                if distance < dist_min:
                    dist_min, _mot = distance, command[i:i + n]
        return dist_min, _mot if location else dist_min

    def add_to_poss(Layer, _add, id_p):
        """Ajoute Layer a possibilites"""
        global seeked
        E = Layer.treat(_add=_add, id_parent=id_p).copy()
        F = {key: E[key] for key in seeked if key in E}
        seeked.update(set(E.keys()))
        possibilites.update(F)

    def act_upon(act):
        """agis sur /act/ et tente de trouver les prochaines étapes"""
        action = act["act"]
        ## si l'action est une sous-branche
        if action.__class__.__name__ == 'layer':
            id = act["choice"]["id"]
            rep_choix[id] = act["choice"].copy()
            # del rep_choix[id]["score"]
            add_to_poss(action, act["choice"]["score"], id)
        ## si l'action est un sous-arbre
        else:
            if action._type == "subtree":
                id = act["choice"]["id"]
                if action._adrS in [tree.address for tree in forest]:
                    add_to_poss(forest[-1].layer1, act["choice"]["score"], id)
            else:
                solved = True
                context = {"requête": command, "score": act, "last_ask": last_ask}
                record(command, action)
                return action.act(context)

    ## préparation
    fen.update()
    global forest
    global seeked
    seeked = set()
    command = DEMAND.get().lower().split() if detail else DEMAND.get().split()
    possibilites = forest[0].layer1.treat().copy()
    for key in possibilites:
        possibilites[key]["id_parent"] = 0
    solved = False
    rep_choix = {}
    ## exécution
    while not solved:
        assert len(possibilites) == 0, print("EMPTY POSSIBILITY FIELD")
        possibility = possibilites[(score_max := max(possibilites.keys()))].copy()
        if possibility["is_cell"]:
            # on cherche à enregistrer la cellule avec l'écart que donne la distance
            dist, mot = cell_norm(possibility, location=True)
            del possibilites[score_max]  # on efface la possibilité
            score = score_max - dist
            possibility["is_cell"] = False  # devient une action
            # décalage au cas d'égalité (edge_case)
            cell = possibility
            while score in possibilites:
                score += np.random.normal(scale=0.001)
            id = np.random.randint(1, 2 ** 30)
            # mémorisation du répertoire action
            possibility["action"] = {'act': cell["_act"],
                                     "choice":
                                         {"id": id, "cell": cell, "layer": cell["origin"],
                                          "parent": cell["id_parent"], "score": dist}}
            possibilites[score] = possibility
        else:
            ## si la possibilité est une action
            act = possibility["action"]
            act_upon(act)
            # print("pdt act", len(possibilites))
            try:
                if act["act"]._type != "subtree":
                    solved, out = True, True
                    break
            except Exception:
                solved = False
            del possibilites[score_max]
        # print("après",len(possibilites))
    global last_ask
    last_ask = command
    ## résolution
    if detail:
        display_choix({}, command)
    else:
        ## selecting choices by order ascending (last first first last, LIFO)
        choice: dict = possibility["choice"]
        decisions = [choice]
        while choice["parent"] != choice["id"]:  # tant qu'on ne touche pas la root
            choice = rep_choix[choice["parent"]]  # on remonte d'un cran dans le procéssus décisionnel
            decisions.append(choice)  # on mémorise l'action
        return decisions


def sep(string, sep_chars=" .-!?,'_"):
    """Renvoie la liste str.split() avec des arguments de splits mieux définis"""

    def split(delimiters, string_, maxsplit=0):
        import re
        regexPattern = '|'.join(map(re.escape, delimiters))
        return re.split(regexPattern, string_, maxsplit)

    separateurs = tuple(sep_chars)
    return split(separateurs, string)


def display_choix(choix, commande, element=None, level=0, n=None):
    def coude(x1, y1, x2, y2, w1=0.4, color='black', widget=Info):
        """dessine le coude entre (x1,y1) et (x2,y2) w1 correspond à la proximité relative entre le coude et (x1,y1)"""
        x1_5 = w1 * x1 + (1 - w1) * x2
        widget.create_line(x1, y1, x1_5, y1, fill=color)
        widget.create_line(x1_5, y1, x1_5, y2, fill=color)
        widget.create_line(x1_5, y2, x2, y2, fill=color)

    coude(10, 10, 690, 690)

    class Grid:
        def __init__(self, command, widget=Info, height=700, width=700, form=(100, 100)):
            self.command = command
            self.form = form
            self.sub_h, self.sub_w = form
            self.w = widget
            self.n, self.p = height // form[0], width // form[1]  # n = nombre de lignes, p nombre de colonnes
            self.grid = []
            self.command = DEMAND.get().split()
            for i in range(self.n):
                self.grid.append([])
                for j in range(self.p):
                    self.grid[-1].append(None)
            self.w_shape = (height, width)
            self.height, self.width = height, width
            widget.bind("<Double-Button-1>", self.double_click)
            widget.bind("<ButtonRelease-1>", self.single_click)
            self.gauche = [[] for _ in range(self.n)]
            widget.bind("<Prior>", self.up)
            widget.bind("<Next>", self.down)
            widget.bind("<ButtonRelease-2>", self.move_v)
            widget.bind("<ButtonRelease-3>", self.add_dem)

        def dist_cell(self, row, col):
            ## gestion des edgecases
            if self.grid[row][col]['type'] == 'tree':
                return 0
            ## gestion des cas normaux :
            dist_min, mot = 2 ** 20, '_____'
            case = self.grid[row][col]
            ## > blank state
            if case["dem"] == ["<blank>"]:
                dist_min = 5
                return dist_min
            ## > normal
            for dem in case["dem"]:
                activateur: list[str] = dem.split()
                n = len(activateur)
                if n == 0:
                    dist_min, mot = 3, '' if 3 < dist_min else dist_min, mot
                    continue
                for i in range(len(self.command) + 1 - n):
                    distance = sum(distance_mot(activateur[k], self.command[i + k]) for k in range(n))
                    if distance < dist_min:
                        dist_min, mot = distance, self.command[i:i + n]
            return dist_min

        def score_cell(self, row, col):
            """renvoie le score final de la cellule de coordonnées (/row/,/col/) et la commande """
            try:
                return self.grid[row][col]["cellscore"]
            except KeyError:
                pass
            if col == 0:
                base = 0
            else:
                i, j = self.last_active(col - 1)
                base = self.grid[i][j]["cellscore"]
            dist = self.dist_cell(row, col)
            scor = base + self.grid[row][col]["sco"] if self.grid[row][col]["type"] == "cell" else base
            self.grid[row][col]["cellscore"] = scor - dist
            return scor - dist

        def add_dem(self, event) -> None:
            """ajoute à la cellule un démarreur."""
            x, y = event.x, event.y
            row, col = y // self.sub_h, x // self.sub_w
            selected = self.grid[row][col]
            if selected is None:
                return
            layer, name = selected["origin"], selected["mot"]
            new_dem = ask("Quel nouveau démarreur dois-je considérer?")
            if new_dem is None:
                return
            layer.value[name]["_dem"].append(new_dem)

        def move_v(self, event):
            """bouge l'écran verticallement"""
            x, y = event.x, event.y
            if y < self.height / 3:
                self.down(event)
            elif y > 2 * self.height / 3:
                self.up(event)

        def single_click(self, event):
            """DEPLOIE UNE BRANCHE"""
            x, y = event.x, event.y
            row, col = y // self.sub_h, x // self.sub_w
            selected = self.grid[row][col]
            global last_select
            last_select = selected
            # print(selected)
            if selected is None:  # if clicked on empty cell
                return None
            elif selected["type"] in ["cell", "tree"]:  # if clicked on tree or cell
                self.handle_cell(row, col)
            else:  # clicked or action
                global clicked_on_cell
                global last_clicked_on_cell
                last_clicked_on_cell = clicked_on_cell = self.grid[row][col]
            if col == 0:
                self.decaler('d')
            self.disp()

        def double_click(self, event):
            """AJOUTE UNE BRANCHE"""
            x, y = event.x, event.y
            row, col = y // self.sub_h, x // self.sub_w
            selected = self.grid[row][col]
            if selected is None:
                return None
            elif selected["type"] in ("cell", "tree"):
                # print(selected)
                layer = selected["cell"]
                create_cell(layer)
            else:
                global clicked_on_cell
                global last_clicked_on_cell
                last_clicked_on_cell = clicked_on_cell = self.grid[row][col]
                if positif(ask("Confirmer l'ajout aux ressources d'entrainement?")):
                    add_training(self.command, selected["action"])
                    say("Finis!")
                else:
                    say("Ok")
            self.disp()

        def handle_cell(self, row, col):
            """gère les cellules de type cellule"""
            ## vider
            self.grid = [[None for j in range(col + 1, self.p)] for i in range(self.n)]
            ## remplir
            self.disp()
            if not self.grid[row][col]["dvp"]:  # si la cellule n'est pas développée
                for r in range(self.n):  # pour chaque ligne
                    try:
                        self.grid[r][col]["dvp"] = False
                    except KeyError:
                        pass
                if col == self.p - 1:
                    self.decaler("g")
                    col -= 1
                if "decalage" not in self.grid[row][col]:
                    self.grid[row][col]['decalage'] = 0
                self.Assign(row, col)
                self.grid[row][col]['dvp'] = True
            else:
                self.grid[row][col]['dvp'] = False
            if col == 0:
                self.decaler("d")

        def Assign(self, row, col):
            """s'ammuse à faire le développement actuel de la cellule"""
            layer = self.grid[row][col]["cell"].treat(base={})
            keys = sorted(list(layer.keys()))
            keys.reverse()
            decalage = self.grid[row][col]["decalage"]
            if decalage < 0:
                decalage = 0
                self.grid[row][col]["decalage"] = 0
            for i in range(self.n):
                try:
                    cell = layer[keys[i + decalage]]
                    name = cell["_act"].__class__.__name__
                    if name == "layer":
                        self.grid[i][col + 1] = {"type": "cell", "dvp": False, "cell": cell["_act"],
                                                 "mot": cell["_nam"], "dem": cell["_dem"], "sco": cell["_sco"],
                                                 "origin": cell["origin"]}
                    elif cell["_act"]._type == "subtree":
                        self.grid[i][col + 1] = {"type": "tree", "dvp": False, "cell": cell["_act"],
                                                 "mot": cell["_nam"],
                                                 "dem": cell["_dem"], "sco": cell["_sco"]}
                    else:
                        self.grid[i][col + 1] = {"type": "action", "mot": cell["_nam"], "action": cell['_act'],
                                                 "dem": cell["_dem"], "sco": cell["_sco"], "origin": cell["origin"]}
                except Exception:
                    self.grid[i][col + 1] = None

        def last_active(self, col=None):
            """renvoie la cellule la plus à droite de la grid qui a dvp = True
            Si col != None, renvoie la cellule de /col/ qui est active"""
            if col is None:
                for j in range(self.p - 1, -1, -1):  # on regarde les colonnes d'abord et on regarde de droite à gauche
                    for i in range(self.n - 1, -1, -1):  # et de bas en haut
                        try:
                            if self.grid[i][j]["dvp"]:
                                return i, j
                        except KeyError:
                            pass
            else:
                for i in range(self.n):
                    try:
                        if self.grid[i][col]["dvp"]:
                            return (i, col)
                    except KeyError:
                        pass
            raise Exception("No active cell was found")

        def up(self, event):
            """fait monter les cases"""
            self.decale("h")

        def down(self, event):
            """fait descendre les cases"""
            self.decale("b")

        def draw_case(self, row, col):
            ## dessin de la case
            y, x = (row + .5) * self.sub_h, (col + .5) * self.sub_w
            if self.grid[row][col] is None:
                return self.w.create_text(x, y, text="")
                # s'occupe des cas pas beaux méchants
            cell_type = self.grid[row][col]["type"]
            choose = {"cell": lambda x, y: self.w.create_oval(x - 40, y - 40, x + 40, y + 40, fill="light sea green"),
                      "action": lambda x, y: self.w.create_oval(x - 45, y - 45, x + 45, y + 45, fill="yellow"),
                      "tree": (lambda x, y: self.w.create_oval(x - 42, y - 42, x + 42, y + 42, fill="lawn green"))}
            f = choose[cell_type]
            if cell_type in ["cell", "tree"]:
                if self.grid[row][col]["dvp"]:
                    self.w.create_oval(x - 46, y - 46, x + 46, y + 46, fill="sea green", outline="dark green")
                    self.w.create_oval(x - 44, y - 44, x + 44, y + 44, fill="azure", outline='dark green')
            if self.grid[row][col] is not None:
                try:
                    i, j = self.last_active(col - 1)
                    x1, y1 = (j + .5) * self.sub_h - 25, (i + .5) * self.sub_w
                    # print("B")
                    coude(x1, y1, x, y)
                except Exception:
                    pass
            f(x, y)
            ## name la case
            texte = self.grid[row][col]["mot"]
            self.w.create_text(x, y - 7, text=texte)
            score_cell = int(self.score_cell(row, col) * 100 + 0.5) / 100
            self.w.create_text(x, y + 7, text=str(score_cell))

        def disp(self):
            self.w.delete("all")
            set(set(self.draw_case(row, col) for col in range(self.p - 1, -1, -1)) for row in range(self.n))

        def decaler(self, direction: str):
            """décale la grid d'une case dans la /direction/
            direction doit apartenir à {"g","d","h","b"}
            et correspond aux directions (dans l'ordre) gauche droite haut bas"""
            gauche = self.gauche  # gauche conserve tous les trucs à gauche.
            # Lors d'un mouvement vers la gauche, on ajoute à droite de gauche
            assert direction in "gdhb" and len(direction) == 1, "Direction invalide"
            if direction == "d":  # on décale tout vers la droite
                if len(gauche[0]) == 0:
                    return None
                else:
                    col = [[gauche[i][-1]] for i in range(self.n)]
                    for i in range(self.n):
                        # print(i,len(col),len(self.grid))
                        self.grid[i] = col[i] + self.grid[i][:-1]
                        del gauche[i][-1]
                        try:
                            self.grid[i][-1]["dvp"] = False
                        except KeyError:
                            pass
            elif direction == "g":
                col = [[None]] * self.n
                for i in range(self.n):
                    gauche[i].append(self.grid[i][0])
                    self.grid[i] = self.grid[i][1:] + col[i]
            else:
                row, col = self.last_active()
                decal = id_list(direction, ["b", 12, "h"]) - 1
                self.grid[row][col]["decalage"] += decal
                self.Assign([row][col])
            self.gauche = gauche  # on re-sauvegarde la matrice gauche

    ## display_choix
    interface = Grid(commande)
    interface.grid[0][0] = {"type": "tree", "dvp": False, "cell": forest[0].layer1, "mot": "--RACINE--"}
    interface.disp()
    interface.grid[2][2] = 'ihapfz'


## sleep_mode

def reset(layer):
    """Resets the score each cell of /layer/ and all of it's children (to 5)
    does not affect subtrees"""
    value = layer.value
    for key in value:
        cell = value[key]
        act = cell["_act"]
        layer.value[key]["_sco"] = 5
        if act.__class__.__name__ == "layer":
            reset(act)


def wait(seconds):
    import time
    time.sleep(seconds)


def sleep():
    """le mode apprentissage de SARA. Scanne toutes les nodes, tous les synonymes, et auste leurs poids."""

    def X(n) -> float:
        """le calcul de X s'effectue après la préparation.
        n_faux_plus     correspond au nombre   d'activations fortuites.
        n_faux_mois     correspond au nombre d'inactivations fortuites
        n_juste         correspond au nombre d'activation correctes
        n_total         correspond au nombre d'apparitions dans la préparation.
        Le but est d'obtenir un X qui correspond à Delta_score_théorique, qui sera ensuite limité"""
        x = n["n_faux_plus"] * n["l_i"] - n["n_faux_moins"] * n["l_ip1"] + (n["n_juste"] / n["n_total"]) \
            * abs(n["l_ip1"] - n["l_i"]) * 0.01
        return x / (n["n_juste"] + n["n_faux_plus"] + n["n_faux_moins"] * 10)

    def Delta_score(node):
        """prends le Delta_score_théorique, le borne, et renvoie alors ce qu'on souhaite.
        La fonction borne est obtenue en intégrant une sigmoide inversée et décallée."""
        f = lambda y, l: -log(exp(l - y) + 1) + log(exp(l) + 1)
        x = X(node)
        l = node["l_i"]
        try:
            return f(x, l)
        except Exception:
            return max(x, l)

    def load_training():
        adress = folder + '/training_log/'
        name = "main.trn"
        try:
            data = pickle.load(open(adress + name, 'rb'))
            pickle.dump(data, open(adress + "bcp.trn", 'wb'))  # le backup a toujours une sauvegarde de moins
        except FileNotFoundError or pickle.PickleError:
            name = "bcp.trn"
            data = pickle.load(open(adress + name, 'rb'))
        return data

    def save_training(data):
        for tree in forest:
            tree.store()
        adress = folder + '/training_log/'
        name = "main.trn"
        pickle.dump(open(adress + name, 'wb'))

    def scan():
        """Renvoie toutes les cellules (qui sont des dict)"""
        cells = []  # l'ensemble de toutes les cellules
        layers = [forest[0].layer1]  # l'ensemble des layers déjà regardé
        layers_a_c = layers[:]  # l'ensemble des layers qui doivent encore être considérées.
        while len(layers_a_c) > 0:
            layer = layers_a_c[0].treat(_add=0, base={})
            scores = sorted(list(layer.keys()))
            scores.reverse()
            for i, score in enumerate(scores):
                l_i = scores[i - 1] - score if i > 0 else scores[i]  # -0
                cell = layer[score]
                cell["l_i"] = l_i
                cells[-1]["l_ip1"] = l_i if i > 0 else 0
                cell["n_juste"] = 1
                cell["n_faux_plus"] = 0
                cell["n_faux_moins"] = 0
                cell["layer"] = layer
                # ajout de la cellule à la liste
                cells.append(cell)
                type_name = cell["_act"].__class__.__name__
                # ajout des éventuelles layers
                if type_name == "layer":
                    if not cell["_act"] in layers:
                        layers_a_c.append(cell["_act"])
                elif cell["_act"]._type == "arbre":
                    condition = True
                    for tree in forest:
                        condition = condition and (tree.address != cell["_act"]._adrS)
                    tree = Arbre(adresse=cell["_act"]._adrS)
                    if condition:
                        forest.append(tree)
                    new_layer = tree.layer1
                    if new_layer not in layers:
                        layers_a_c.append(new_layer)
            layers.append(layers_a_c[0])
            del layers_a_c[0]
        cells[-1]["l_ip1"] = 0
        return cells

    def teste(cells, training):
        """Pour l'ensemble des cellules, pour l'ensemble des questions de training,
        vérifie que l'utilisation des cellules est correcte.
        
        training : {question1:reponse1 (sous forme stored) ,question2:reponse2...}
        
        où réponse est le nom de l'action à effectuer"""

        def lead_right_answer(node, answer):
            try:
                if answer._name == node["_act"]._name:
                    return True
            except KeyError:
                pass
            action = node["_act"]
            condition = (action.__class__.__name__ == "layer")
            if condition:
                layer = action
            elif action._type == "subtree":
                condition = True
                tree = None
                for arbre1 in forest:
                    if arbre1.address == action._adrS:
                        tree = arbre1
                if tree is None:
                    tree = Arbre(address=action)
                    forest.append(tree)
                layer = tree.layer1
            if condition:
                for node2 in layer.value.values():
                    root.update()
                    if lead_right_answer(node2, answer):  # si UN fonctionne
                        return True
            else:
                return False

        def cell(node, cells):
            """trouve la cell de la liste cells qui correspond à node"""
            for cell_ in cells:
                if cell_["_nam"] == node["_nam"]:
                    if cell_["_dem"] == node["_dem"] and cell_["_sco"] == node["_sco"]:
                        return cell_

        # print(training)
        ## test (fait actuellement partie de teste)
        for exercice in training.items():
            question, reponse = exercice[:2]
            ## résolution de la demande (solve) et vérification de l'exactitude
            thinking_process = solve(False, question)
            answer = thinking_process[0]  # thinking process est renversé: Les premières décisios sont à la fin
            right_limit = 0  # le nombre d'étapes à remonter avant d'être juste
            if reponse != answer["cell"]["_act"].store():
                ## en cas d'erreur, remonter jusqu'à la source
                layer = answer["cell"]["origin"]
                # retourne la node de thinking process qui appartient 
                NODING = lambda layer, element: layer.value[element["cell"]["_nam"]]
                node = NODING(layer, 0)
                for element, i in enumerate(thinking_process[1:]):
                    if lead_right_answer(node, reponse):
                        break
                    layer = element["cell"]["origin"]
                    # print(layer)
                    node = NODING(layer, element)
                node_f_p = NODING(element["cell"]["origin"], element)
                C = cell(node_f_p, cells)  # on prends la cellule qui a tout fait foirer
                C["n_faux_plus"] += 1
                for cell_moins in layer.value.values():
                    if lead_right_answer(cell_moins, reponse):
                        cell_moins["n_faux_moins"] += 1
                        break
            corrects = thinking_process[i:]
            for level in corrects:
                node = level["cell"]
                C = cell(node, cells)
                C["n_juste"] += 1

    def fonctionnement(event):
        """consiste en la réelle fonctionnalité de <sleep>"""
        training = load_training()
        # print(training)
        global working
        A.start(1)
        root.update()
        working = True
        cells = scan()
        ## début algo
        while not last_sleep_cycle:
            teste(cells, training)
            r = np.random.random()
            if r < .1:
                print("== Remise à niveau ==")
                moy = sum(cell["_sco"] for cell in cells) / len(cells)
            else:
                print("=== DREAM ===")
            for cell in cells:
                root.update()  # to put in each cycle
                layer = cell["origin"]  # on récupère l'objet destinataire
                if r < .1:
                    print(cell["_nam"], "|", cell["_sco"], "=>", cell["_sco"] ** .5 * 10 / moy)
                    layer.value[cell["_nam"]]["_sco"] = cell["_nam"][
                                                            "_sco"] ** 0.5 * 10 / moy  # on remet les valeurs autour de la moyenne
                else:
                    D_score = Delta_score(cell)  # on récupère la modification
                    print(D_score, cell["_nam"])
                    layer.value[cell["_nam"]]["_sco"] += D_score  # on met à jour
        ## fin algo
        A.stop()
        working = False

    ## interface :
    if not fen_opened:
        root = Tk()
        root.title("Sleep mode")
        root.iconbitmap(folder + '\\sara_1_icon.ico')
    else:
        root = Toplevel(fen)
        fen.title("SARA 1 - Asleep")
        root.transient(fen)
        root.title("Sleep mode")
        root.iconbitmap(folder + '\\sara_1_icon.ico')
    global last_sleep_cycle
    global working
    working = False
    last_sleep_cycle = True

    def set_as_last_sleep_cycle():
        global last_sleep_cycle
        last_sleep_cycle = not last_sleep_cycle
        if last_sleep_cycle:
            Wake.configure(image=Wake.img1)
        else:
            Wake.configure(image=Wake.img2)
            if not working:
                try:
                    fonctionnement("blop")
                except Exception:
                    fen.title("SARA 1")
            fen.title("SARA 1")

    Wake = Button(root, command=set_as_last_sleep_cycle)
    Wake.img1 = ImageTk.PhotoImage(Image.open(folder + "/images/wake_icon.png"))
    Wake.img2 = ImageTk.PhotoImage(Image.open(folder + "/images/sleep_icon.png"))
    Wake.pack(side=LEFT)
    Button(root, text="Quitter", command=root.destroy).pack(side=RIGHT)
    A = ttk.Progressbar(root, orient=VERTICAL, length=20)
    set_as_last_sleep_cycle()
    root.mainloop()
    fen.title("SARA 1")


def flatten(list_instance):
    """
    [[2,3,3],[2,5,6]] -> [2,3,3,2,5,6]
    """
    flat = []
    for sub_l in list_instance:
        flat += sub_l if isinstance(sub_l, list) else [sub_l]
    return flat


dictionnaire = set(synonymes.keys())


def id_list(element, liste):
    for i in range(len(liste)):
        if liste[i] == element:
            return i
    return -1


def up_key_press(event):
    """charge à la place une demande précédente"""
    pass


def down_key_press(event):
    """charge à la place une demande précédente"""
    pass


def positif(t):
    if t in ["oui", "o", "Oui", "y", "positif", "bien sûr", "OUI", 'yes', 'Yes', 'O', 'Y']:
        return True
    else:
        if not t:
            raise Exception("Empty check. Might be due to interruption")
        command = t.split()
        pos = [distance_mot(command[i], 'oui') for i in range(len(command))]
        neg = [distance_mot(command[i], 'non') for i in range(len(command))]
        return min(pos) < min(neg)


def fits(word, word_list):
    """Renvoie vrai ssi /word/ est dans /word_list/"""
    threshold = lambda n: 2 + 0.5 * sqrt(n) * log(1 + (n / 10))
    return min(distance_mot(word, mot) for mot in word_list) < threshold(len(word))


def w_correct(mot: str) -> str:
    """On corrige le mot"""
    return mot if mot in dictionnaire else min(dictionnaire, key=lambda word: Lev(mot, word))


def distance_mot(mot1, mot2, limite=-1, returned=True):
    """renvoie la distance entre deux mots, composée de la distance sémantique et de la distance orthographique
    La limite a une valeur par défaut de -1, et quand positive, correspond à la distance maximale au dela de laquelle on arrête de regarder et on renvoit un infini (2 ^20")"""
    if (not mot1 in synonymes.keys()) and returned:
        return distance_mot(mot2, mot1, limite=limite, returned=False)
    D1 = d_O(mot1, mot2)
    if limite < 0:
        limite = D1
    else:
        limite = min((D1, limite))
    try:
        D2 = d_S(mot1, mot2, limite)
    except Exception:
        return D1
    return min({D1, D2})


def add_synonyme(mot, syn, distance):
    """Ajoute un synonyme (/syn/) à /mot/ avec une distance de /distance/"""
    global synonymes
    if not mot in synonymes:
        synonymes[mot] = {}
    if not syn in synonymes[mot]:
        synonymes[mot][syn] = distance
    else:
        synonymes[mot][syn] = min(synonymes[mot][syn], distance)
    pickle.dump(synonymes, open(folder + "/language ressources/syn_dict", 'wb'))


def str_to_dict(str_dict):
    """If a string is the result of str(/dict/),
    then str_to_dict can, from that sting, find back the /dict/"""
    t = "answer = " + str_dict
    L = {}
    exec(t, globals(), L)
    dict = L["answer"]
    return dict


def syn(mot) -> set[tuple[str, float]]:
    """renvoie [(syn1,score1),(syn2,score2)] """
    synonymes.setdefault(mot, {})
    return set(list(synonymes[mot].items()))


def inf(mot: str) -> str:
    """renvoie l'infinitif d'un mot (ou la forme masculin singulier pour un nom, etc...)"""
    for truc in conjugues:
        if mot in truc:
            return truc[0]
    else:
        return None


def conj(mot, vb):
    """renvoie vrai si le /mot/ est une forme conjuguée (ou accordée) de /vb/"""
    for truc in conjugues:
        if vb in truc:
            return mot in truc
    return False


def create_cell(layer):
    """ajoute une cellule à /layer/"""
    A = ask("mot d'activation?", hover="seulement\n\t<blank>\t\npour une cellule par défaut")
    if A is None:
        return
    cell = {'_dem': [A.strip('"')], }
    ## nommer la cellule
    if positif(ask("Cette cellule doit-elle avoir un nom?")):
        cell["_nam"] = ask("Quel nom ?")
        ## rajouter des démarreurs
        while positif(ask("Un autre mot d'activation est-il requis?",
                          hover="Ces mots (ou des similaires) doivent être compris dans la question pour que cette cellule soit active.")):
            activateur = ask("mot d'activation?")
            if activateur:
                cell["_dem"].append(activateur)
    ## nature de la cellule
    if positif(ask('Est-ce une nouvelle branche?')):
        cell['_act'] = Arbre.Layer()
    else:
        cell['_act'] = Arbre.Action()
    layer + cell
    say('Finis!', 1)


def check_permutation(mot):
    """regarde dans le dictionnaire des synonymes toutes les variations possible.
    Prend la plus proche, la renvoie avec sa distance d_O"""
    min_mot = ""
    min_m = 2 ** 21
    for base in synonymes:
        D = Lev(mot, base)
        if D == 0:
            return 0, base
        elif D < min_m:
            min_mot = base
            min_m = D
    return min_m, min_mot


def conjuguaisons(mot) -> set[tuple[str, float]]:
    """renvoie l'ensemble des conjuguaisons possibles de /mot/"""
    retour = set(word for conjug in conjugues for word in conjug if mot in conjug)
    return set([el, 0.5] for el in retour)


def d_S(mot1, mot2, radius):
    """distance sémantique entre mot1 et mot2.Arrête de rechercher aprés radius.
    """
    assert radius > 0, "{} is a negative radius. Something went wrong".format(radius)
    # on ne met pas de condition mot1 == mot2 parce que c'est la première chose que la boucle regarde
    points_to_words_map = {0.: mot1}  # points est l'ensemble des mots avec lesquels on considère un lien sémantique
    already_considered = {}
    score = {0, }
    # djikstra's algo on the words
    while (min_score := min(score)) < radius:
        ## we now consider the closest point
        cur_closest_for_inspection = points_to_words_map[min_score]
        if cur_closest_for_inspection == mot2:  # si trouvé (et ce avec son chemin d'aparition le plus court)
            return min_score
        # and mark it as already considered
        already_considered[min_score] = cur_closest_for_inspection
        del points_to_words_map[min_score]
        # and add make the point_to_cords_map flourish ! ;)
        new_points = syn(cur_closest_for_inspection).union(conjuguaisons(cur_closest_for_inspection))
        # new_points vaut {(syn1,distance1),(syn2,distance2),...}
        for point in new_points:
            point[1] += min_score  # on rajoute à la nouvelle distance parcourue l'ancienne => distance totale
            if point[0] not in already_considered.values() and point[1] < radius:  # if point can be considered !
                while point[1] in points_to_words_map:
                    point[1] += np.random.normal(scale=0.001)
                points_to_words_map[point[1]] = point[0]  # on rajoute nouv à points
        if len(new_points) == 0 and len(points_to_words_map) == 0:
            difference_permutation, blop = check_permutation(cur_closest_for_inspection)
            # on retient le mot du dictionnaire des synonymes le plus proche, ainsi que la différence qu'il génère
            new_dist = min_score + difference_permutation
            if new_dist < radius:
                while new_dist in points_to_words_map:
                    new_dist += np.random.normal(scale=0.001)
                points_to_words_map[new_dist] = blop
        score = set(points_to_words_map.values())
    return float("infinity")


def d_O(mot1, mot2):
    """distance orthographique entre mot1 et mot2"""
    if (mot1 in prenoms and mot2 == '_prenom_') or (
            mot2 in prenoms and mot1 == '_prenom_'):  # détecte l'usage de prénoms
        return .0001
    elif mot2 in conjuguaisons(mot1):
        return 0.3
    V = Lev(mot1, mot2)
    return V ** (1 + (V / len(mot2)) * sigm(V - len(mot2) ** .5))


def Lev(s, t):
    ## setting the matrice up
    mat = []
    for i in range(len(t) + 1):
        mat.append([])
        for j in range(len(s) + 1):
            if i == 0:
                mat[-1].append(j)
            elif j == 0:
                mat[-1].append(i)
            else:
                mat[-1].append(0)
    ## setting the cost up
    cost = []
    for i in range(len(t)):
        cost.append([])
        for j in range(len(s)):
            if str.lower(s[j]) == str.lower(t[i]):
                cost[-1].append(0)
            else:
                cost[-1].append(1)
    ## calculations
    for i in range(1, len(t) + 1):
        for j in range(1, len(s) + 1):
            a = mat[i - 1][j] + 1
            b = mat[i][j - 1] + 1
            c = mat[i - 1][j - 1] + cost[i - 1][j - 1]
            mat[i][j] = min(a, b, c)
    return mat[-1][-1]


def add(layer):
    """Réalise l'addition de  sur layer"""
    dic = {}
    dic["_dem"] = [w_correct(ask("Quel démarreur dois-je utiliser?"))]
    if dic["_dem"][0] in layer.value:
        dic["_nam"] = ask("Quel nom devra cette action avoir?")
    if positif(ask("Cela correspond-il à une action?")):
        dic["_act"] = Arbre.Action()
    else:
        dic['_act'] = Arbre.Layer()
    layer + dic


class Arbre:
    class Layer:

        def __init__(self, load=False):
            """
            _dem : démarreurs (list)
            _nam : nom       (str)
            _act : action    (layer) ou (action)
            _sco : score     (1D number)
            """
            self.value = {}
            if load:
                for el in load:
                    if self.est_bien_forme(el):
                        do = True
                        # print(el)
                        try:
                            el["_act"] = Arbre.Layer(el["_act"])
                        except ValueError:
                            try:
                                el["_act"] = Arbre.Action(el["_act"])
                            except Exception:
                                do = False
                        if do:
                            self.__add__(el)
                        else:
                            say("{} n'a pas été rajouté par absence d'action en état de fonctionnement.".format(el))
                    else:
                        raise ValueError("{} n'a pas été rajouté par erreur de mémorisation évidente.".format(el))

        @staticmethod
        def est_bien_forme(data):
            condition = isinstance(data, dict)
            if "_dem" in data:
                condition = condition and isinstance(data["_dem"], list)
                if "_nam" in data:
                    condition = (condition and isinstance(data["_nam"], str))
                if "_sco" in data:
                    condition = (condition and type(data["_sco"]) in [type(1), type(0.2), type(1 + 0j)])
                return condition
            return False

        def __add__(self, data):
            """/data/ est une cellule (cell)
            Ainsi, /data/ est de la forme :
            {'_dem':liste de démarreurs,
            '_act':action de la cellule. Peut être un layer,
            '_sco': le score correspondant à la cellule. Vaut par défaut 10.
            '_nam' : est optionnel. Il correspond au titre}
            """
            assert self.est_bien_forme(data), "Incorrect {} addition type".format(data)
            demarreurs = data['_dem']
            action = data["_act"]
            title = data["_nam"] if "_nam" in data else demarreurs[0]
            score = data["_sco"] if "_sco" in data else (
                x if (x := avg([cell["_sco"] for cell in self.value.values()])) != 0 else 5
            )
            if title in self.value:
                if self.value[title]["_dem"] == demarreurs and self.value[title]["_act"] == action:
                    self.value[title]['_sco'] += score
                else:
                    if not positif(ask("{} est déjà une entrée valide. Ecraser?\n".format(title))):
                        say("Compris")
                        return None
            else:
                self.value[title] = {"_nam": title, "_sco": score, "_dem": demarreurs, "_act": action}

        def title_act(self, action):
            """Prends une action, et renvoie le titre correspondant. Renvoie None si l'action n'est pas incluse"""
            for title in self.values:
                if self.values[title]["_act"] == action:
                    return title
            else:
                return None

        def action(self, mot):
            """si mot est un démarreur valable, alors renvoie l'action correspondante.
            Sinon, renvoie None"""
            score_c = 0
            choisis = None
            for title in self.value:
                if mot in self.value[title]["_dem"]:
                    if self.value[title]["_sco"] >= score_c:
                        choisis = self.value[title]["_act"]
                        score_c = self.value[title]["_sco"]
            return choisis

        def copy(self):
            """returns unlinked copy of the present layer"""
            return Arbre.Layer(self.store())

        def cherche(self, mot):
            """Soit /optimal/ le mot qui rentre le mieux dans toute la layer.
            cherche renvoie 
            
            [optimal,d(optimal,mot)] avec 
            
            d(mot1,mot2) = min(dSens(mot1,mot2),dOrtho(mot1,mot2)"""
            pass

        def ajouter_demarreur(self, title, dem):
            assert (title in self.value) or self.title_act(self.action(title)) != None, "{} not found".format(title)
            if title not in self.value:
                title = self.title_act(self.action(title))
            if dem in self.value[title]['_dem']:
                pass
            else:
                self.value[title]["_dem"].append(dem)

        def create(self, dem1, action, score=10):
            """crée une nouvelle value dans la layer. Dans le futur, ajustera son score automatiquement pour
            s'assurer qu'elle fonctionne bien. """
            self.__add__({"_dem": [dem1], "_act": action, "_sco": score})

        def treat(self, _add=0, base={}, id_parent=None):
            """prends un layer et le désèque, donnant ainsi un rang loufoque de possibilités"""
            possibilities = base
            a = list(self.value.keys())
            for nam in a:
                score = _add + self.value[nam]["_sco"]
                while score in possibilities:
                    score += np.random.normal(scale=0.001)
                possibilities[score] = self.value[nam]
                possibilities[score]["origin"] = self
                if id_parent is not None:
                    possibilities[score]["id_parent"] = id_parent
                # to check whether possibility has been added via treat
                possibilities[score]["is_cell"] = True
            return possibilities

        def store(self):
            """renvoie une version simplifiée de la layer, plus aisément stockée"""
            stored = []
            A = self.value.copy()
            for key in list(A.keys()):
                el = A[key].copy()
                el["_act"] = el["_act"].store()
                # print(el != self.value[key])
                stored.append(el)
            return stored

    class Action:

        def __init__(self, load=None):
            """
            _name : type (str)
            _type : action type (str) dans {subtree,command(e)}
            
            -------------------------si _type == subtree ---------------------------
            _adrS : adresse(str) 
                    adresse du subtree recherché sur le dictionnaire.
                    Remplace /here/ et /ici/ par l'adresse du dossier contenant ce programme
            ----------------si _type == command or type == commande-----------------
            _ansR : answer(boolean)
                    indique si l'action est une réponse
                ----------------------si __ansR -----------------------------       
                _say_ : réponse (str)
                _flex : flexibilité(float)
                        indique la capacité qu'a SARA a modifier la réponse
                        plus flex est grand, plus la réponse sera modifiable
                        (correspond à la distance max entre la réponse voulue et la réponse donnée)
                ----------------------si not __ansR -------------------------       
                _cmd_ : commande(str)
                _Tinp : text_input(boolean)
                        -si vrai, tente de faire exécuter la commande par SARA
                        -si faux, ou si SARA n'y arrive pas, se rabat sur Python
            """
            if load is not None:
                ## load
                if self.est_bien_forme(load):
                    self._name = load["_name"]
                    self._type = load["_type"]
                    if self._type in ['command', "commande"]:
                        self._ansR = load["_ansR"]
                        if self._ansR:
                            self._say_ = load["_say_"]
                            self._flex = load["_flex"]
                        else:
                            self._cmd_ = load["_cmd_"]
                            self._Tinp = load["_Tinp"]
                    elif self._type == "subtree":
                        self._adrS = load["_adrS"]

                    else:
                        raise Exception("Ununderstood or altered {} action type".format(load))
                else:
                    raise Exception("Ununderstood or altered {} action".format(load))
            else:
                say("== Créateur d'action ==",
                    hover="Les actions s'affichent en jaunes, et correspondent à la décision finale de SARA ")
                ## create
                self._name = scrub(
                    ask("Une idée de nom à utiliser?", hover="Le nom de l'action en cours de définition"))
                say("Compris. Mémorisé en tant que {}".format(self._name))
                # assignation du type
                self._type = ask("Quel type d'action?", hover="Parmis subtree et commande")
                if distance_mot(self._type, "commande") < distance_mot(self._type, "subtree"):
                    self._type = "command"
                else:
                    self._type = "subtree"
                # création en fonction du type
                if self._type in ['command', "commande"]:
                    self._ansR = positif(ask("Est-ce une réponse?", hover="Lors de l'activation renvoie du texte pur"))
                    if self._ansR:
                        self._say_ = ask("Que dois-je dire?")
                        self._flex = float(ask("Avec quelle précision", hover='Non implémenté. Merci de mettre 0'))
                    else:
                        self._Tinp = positif(ask("Vais-je devoir traiter cette commande moi-même?",
                                                 hover="""Si oui, la commande va passer par la résolution de SARA. Utile pour des raccourcis, mais lent"""))
                        self._cmd_ = ask("Quelle est cette commande?",
                                         hover="""Si vous avez répondu précédemment oui, écrivez une phrase simple. Sinon, Prenez garde à activer vos fonction avec : 'answer_var = /fonction/(context)' si la fonction nécéssite le contexte. Il est essentiel que /answer_var/ soit définie. """)
                elif self._type == "subtree":
                    self._adrS = ask("Merci d'écrire la réponse juste dessous!")
                else:
                    raise Exception("Ununderstood or altered {} action type".format(load))
                say("L'action a bien été créée !")

        def est_bien_forme(self, data):
            condition = type(data["_name"]) == type('')
            condition = condition and type(data["_type"]) == type('')
            c = [False] * 6
            for i in range(6):
                datapoint = ["_adrS", "_ansR", "_say_", "_flex", "_cmd_", "_Tinp"][i]
                datatype = [type(''), type(condition), type(''), type(2.1), type(''), type(condition)][i]
                try:
                    c[i] = (type(data[datapoint]) == datatype)
                except:
                    c[i] = False
                # print(condition ,c)
            condition = condition and (c[0] or (c[1] and ((c[2] and c[3]) or (c[4] and c[5]))))
            return condition

        def act(self, context):
            if self._type == "subtree":  # charge l'arbre
                global forest
                for i in range(len(forest)):
                    tree = forest[i]
                    if tree.address == self._adrS:
                        return i
                arbre = Arbre(address=self._adrS)
                forest.append(arbre)
                return -1  # renvoie le rang de l'arbre planté
            else:
                if self._ansR:
                    say(self._say_, self._flex)
                else:
                    condition = self._Tinp
                    if condition:
                        try:
                            solve(_cmd_)
                        except Exception:
                            say("La résolution a échoué. Essayons avec python.")
                            condition = False
                    if not condition:
                        L = locals().copy()
                        exec(self._cmd_, globals(), L)
            try:
                return L["answer_var"]
            finally:
                return None

        def store(self):
            return self.__dict__

    ## gestion des arbres

    def __init__(self, load=None, address=None):
        """
        adress : adresse dans laquelle le tree sera mémorisé
        """
        ## chargement avec l'adresse donnée
        try:
            pre_load = load
            load = pickle.load(open(folder + '/log storage/' + address, 'rb'))
            if pre_load == load:
                say("Que c'est gentil! {} a été donné deux fois!".format(load))
        except Exception:
            print("empty adress. Attempting to create new tree")
            None
        if load is None:  # si on a des des données de chargements.
            try:
                self.address = load["adress"]
                try:
                    self.layer1 = Arbre.Layer(load=load["layer"])
                except Exception:
                    self.layer1 = Arbre.Layer()
            except Exception:
                raise Exception("{} is incorrect loading data".format(load))
        else:
            if address:
                self.address = address
            else:
                self.address = ask("Merci de donner l'adresse de mémorisation.")
            self.layer1 = Arbre.Layer()

    def store(self):
        """mémorise l'arbre.
        Renvoie le load(nécessaire à l'__init__, mais il n'est absolument pas nécessaire de le récupérer,
        car le fichier aura déjà été traité & mémorisé!)"""
        memoire = {"layer": self.layer1.store(), "adress": self.address}
        pickle.dump(memoire, open(folder + '/log storage/' + self.address, 'wb'))

    def cut(self):
        """looks for the most heavy layer and makes it into a subtre"""
        ## looks for the most heavy layer
        layer = self.layer1
        m_size, m_i = 0, 0
        for A in layer.value:
            a = layer.value[A]
            if a['_act'].__name__ == 'layer':
                s = a['_act'].__sizeof__()
                if s > m_size:
                    m_size = s
                    m_i = A
        if m_i == 0:
            say('La tâche est impossible', 0.1)
            return None
        else:
            ST = Arbre(load={{"layer": layer.value[m_i], "adress": ask('Nouvelle adressse?')}})
            self.backup()
            load = {'_name': ST.address, '_type': 'subtree', '_adrS': ST.address}
            layer.value[m_i]['_act'] = Arbre.Action(load=load)

    def backup(self):
        """réalise un backup"""
        memoire = {"layer": self.layer1.store(), "adress": self.address}
        pickle.dump(memoire, open(folder + '/log storage/' + self.address + '_backup', 'wb'))


sigma = lambda z: 1 / (1 + np.exp(-z))


def agir(couple, end='\t'):
    print(couple, end=end)


def decompose(phrase):
    cut = phrase.split()
    for i in range(len(cut)):
        mot2 = cut[i]
        for j in range(i + 1):
            mot1 = cut[i - j]
            if j == i:
                end = '\n'
            else:
                end = '\t\t'
            agir((mot1, mot2), end)


## - PETRA (Personality Emulator Through Request Adaptation)

## gestion de la database
import sqlite3
import datetime
import time

file_name = "DATABASE.db"
connection = sqlite3.connect(file_name)
cursor = connection.cursor()

cursor.execute(
    "CREATE TABLE IF NOT EXISTS word_equivalence (id INTEGER PRIMARY KEY AUTOINCREMENT, mot1 TEXT, mot2 TEXT,executable BLOB)")
cursor.execute("CREATE TABLE IF NOT EXISTS blabla (id INTEGER PRIMARY KEY AutoINCREMENT, nom TEXT, value BLOB)")


# une table de mémoire a trois colonnes : 'id' (key), 'nom' (activateur), 'valeur' (objet désiré)
# une table peut disposer d'une ligne nommée 'standard_action21', auquel cas elle opère cette action à chaque élément de chaque fetch

def similar_words(mot):
    """Renvoie la liste des mots similaires retenus par l'utilisateur (propre à SARA)
    En cas d'exécutables, merci de se réferrer """
    D = {"mot": mot}
    cursor.execute("""SELECT mot2, executable FROM word_equivalence WHERE mot1 = :mot""", D)
    list_ = cursor.fetchall()
    connection.commit()
    answer = []
    for i, tup in enumerate(list_):
        if tup[1]:
            local = locals.copy()
            exec(tup[1], globals, local)
            answer.append(local["result"])
        else:
            answer.append(tup[0])
    return answer


def fetch(origin, identifier=None):
    """Va chercher l'information de la table /origin/. Par défaut renvoie la table.
    Si identifier n'est pas None, alors va chercher la ligne avec ce nom."""
    origin = closest_table(origin)
    print(origin)
    cursor.execute("SELECT nom,value FROM " + scrub(origin))
    D = dict(cursor.fetchall())
    if None == identifier:
        return list(D.values())
    rep = []
    for key in D:
        if fits(identifier, [D[key], key]):
            rep.append(D[key])
    return rep


def pull(destination, identifier):
    """Supprime la ligne où le nom ou la value vaut /identifier/"""
    D = {"table": destination, "id": identifier}
    ## test d'unicité
    cursor.execute("SELECT * FROM " + scrub(destination) + " WHERE :id == nom OR :id == value", D)
    L = cursor.fetchall
    if len(L) == 0:
        say("Aucun objet avec {} comme identifiant trouvé".format(scrub(identifer)))
    elif len(L) > 1:
        say("Plusieurs objets correspondant à {} ont étés trouvés".format(scrub(identifier)))
        if not positif(ask("Confirmez la supression des {} éléments ?".format(len(L)))):
            return None
    else:
        if not positif(ask("Confirmez la supression del'élément ?".format(len(L)))):
            return None
    say("Suppression confirmée")

    ## suppression

    cursor.execute("DELETE FROM :table WHERE :id == nom OR :id == value", D)
    connection.commit()
    say("Supression effectuée")


def place(destination, nom, value):
    """Rajoute à la table /destination/ l'/objet/"""
    ## finding destination
    destination = closest_table(destination)
    D = {"destination": destination, "value": value, "nom": nom}
    ## finding whether to modify value
    cursor.execute("SELECT value FROM " + scrub(destination) + " WHERE nom == 'treatment_on_creation';")
    R = cursor.fetchall()
    if R:
        code = R[0][0]

        def f(x):
            L = {"code": code, "x": x}
            teste_code(code)
            exec(code, globals(), L)
            return L['result']
    else:
        f = lambda x: x
    value = f(value)
    D["value"] = value
    print(value)
    ## pushing value into place
    cursor.execute("INSERT OR REPLACE INTO " + scrub(destination) + " (nom,value) VALUES (:nom,:value)"
                   , D)
    assert cursor.lastrowid != 0, "Placement of last row went wrong. \n Last variable touched : {}".format(D)
    connection.commit()


def scrub(t):
    """S'assure qu'aucun opérateur ne reste dans la chaine de caractère."""
    return ''.join(chr for chr in t if (chr.isalnum() or chr in "_"))


def new_value(destination, nom, value, check=True):
    """Remplace la valeur dans la Base de donnée /destination/ dans la case de nom /nom/ par /value/.
    Par défaut demande une confirmation."""
    if check:
        if not positif(ask("L'ancienne valeur était de {}. Voulez vous vraiment confirmer le changement vers {}".format
                               (fetch(destination, identifier=nom), value))):
            return None
    D = locals()
    cursor.execute("UPDATE " + scrub(destination) + " SET value = :value WHERE nom = :nom")
    connection.commit()


def create_table(table_name, treatment_on_creation=None):
    """Crée une table
    Treatment est une opération à effectuer à toutes les valeurs dès récupérées"""
    cursor.execute("CREATE TABLE " + scrub(table_name) + "(id INTEGER PRIMARY KEY,nom TEXT, value BLOB)")
    connection.commit()
    if treatment_on_creation:
        place(table_name, "treatment_on_creation", treatment_on_creation)
    say("Table {} créée avec succés !".format(table_name),
        hover="Afin d'assainir cette demande, le vrai nom est {}".format(scrub(table_name)))


def teste_code(code):
    """Teste une str qui est un code
    Par défaut, on cosidère que None n'est pas une valeur qui peut être renvoyée.
    Un code est considéré comme fonctionnel s'il renvoie une valeur dans la variable /result/
    
    teste_code peut renvoyer [True] si le code doit rajouter 'result = {}',ie si la variable result ne renvoie rien
    ce True passe les tests de condition (if,while,etc...), mais ne passe pas le test teste_code(code) == True"""
    L = {}
    try:
        exec(code, globals(), L)
    except Exception:
        say("Le code proposé ne fonctionne pas")
        return False
    if "result" in L:
        return True
    else:
        return [True]  # teste code peut renvoyer [True] si le code doit rajouter 'result = {}'


def add_significance(mot1, mot2):
    """Ajoute un sens à ce mot (des versions ultérieures combineront ce procédé avec celui de BRAIN pour obtenir un mélange parfait)
    Permet l'ajout de valeurs movibles (dépendant de fonctions), comme, par exemple
      > 'aujourd'hui' = str(datetime.datetime.now().date()) # le jour d'aujourd'hui sous forme
      > 'demain'      = lendemain(/aujourd'hui/)
      """
    ex = positif(ask("Le second mot ({}) est-il un exécutable?".format(mot2),
                     hover="par exemple 'aujourd'hui, dont la valeur doit varier par des paramêtres externes"))
    if ex:
        glorp = 'executable'
        condition = teste_code(mot2)
        if condition and condition is not True:
            # teste code peut renvoyer [True] si le code doit rajouter 'result = {}'
            # rajoutons le 'result = '
            mot2 = 'result = ' + mot2
            print(mot2, condition)
        else:
            say("Interruption de la requête...")
            raise Exception("INVALID COMMAND")
    else:
        glorp = "mot2"
    D = {"mot1": mot1, "mot2": "", "executable": None, glorp: mot2}
    cursor.execute("INSERT INTO word_equivalence (mot1,mot2,executable) VALUES (:mot1,:mot2,:executable)", D)
    connection.commit()


def ensemble_des_tables():
    """Renvoie la liste des tables comprises dans la DataBase"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type == 'table'")
    L1 = cursor.fetchall()
    # L1 = [(name1,),(name2,)...] on veut [name1,name2,...]
    L = [t[0] for t in L1]
    return L


def ensemble_des_tables_reduced():
    L = ensemble_des_tables()
    liste = []
    for subList in L:
        if subList in ["word_equivalence", 'sqlite_sequence']:
            continue
        else:
            liste.append(subList)
    return liste


def delete_table(table):
    """Supprime la table /table/"""
    if table not in ensemble_des_tables():
        table = closest_table(table)
    if positif(ask("Voulez-vous confirmer la supression de la table {}?".format(table),
                   hover="Une table est une mini base de donnée qui regroupe les informations ensembles. "
                         "Par EX: Calendrier")):
        cursor.execute("DROP TABLE IF EXISTS :table", {"table": table})
        connection.commit()


def closest_table(to):
    """Returns the closest table name to /to/"""
    t = scrub(to)
    i_min = 0
    L = ensemble_des_tables_reduced()
    # cas rapide (t c L)
    if t in L:
        return L[id_list(t, L)]
    assert len(L) > 0, "Empty DataBase"
    answer = min(L, key=lambda word: distance_mot(word, t))
    return answer


## gestion de protocoles
import threading
import pickle


class Protocoles:

    def __init__(self, cmd='', condition=[], load=None):
        """condition est soit :
        * une str qui contient un test qui renvoie True ou False
        * une list de str qui contiennent ces mêmes tests.
        Par défaut, s'active si les tests de condition sont toutes vraie.
        ----------------------------------------------------------------
        La cmd, si elle renvoie quelque-chose, doit le faire dans la variable /result/
        """
        if load:
            self.tries = load["tries"]
            self.executions = load["executions"]
            self.cmd = load["cmd"]
            self.condition = load["condition"]
            if not "name" in load:
                try:
                    self.name = ask("Quel nom donner au protocole qui {}".format(self))
                except:
                    self.name = input("Quel nom ce protocole doit-il avoir ?")
            else:
                self.name = load["name"]
        else:
            self.name = ask("Quel nom ce protocole doit-il avoir ?")
            self.tries = 0
            self.executions = 0
            self.cmd = cmd
            self.condition = condition

    def test(self):
        """Si la condition d'activation est réalisée, active la commande"""
        self.tries += 1
        if type(self.condition) != type(list()):
            self.condition = [self.condition]
        for test in self.condition:
            l = {}
            exec(test, globals(), l)
            truth = l["result"]
            if not truth:
                return None
        self.__run__(l)

    def success_rate(self):
        return self.executions / self.tries

    def __run__(self, l=None):
        self.executions += 1
        result = None
        if not l:
            l = locals().copy()
        exec(self.cmd, globals(), l)
        return l["result"]

    def __str__(self):
        return 'réalise {} quand {}'.format(self.cmd, self.condition)

    def store(self):
        mem = {"name": self.name, "cmd": self.cmd, "condition": self.condition, "tries": self.tries,
               "executions": self.executions}
        return mem


class Agenda_prot(Protocoles):
    """Bypasses the test function"""

    def __init__(self):
        self.name = "-AGENDA-"
        self.tries = 0
        self.executions = 0
        self.cmd = "avertit d'un évênement"
        self.condition = "cet évènement est réalisé"

    def test(self):
        """Si la condition d'activation est réalisée, active la commande"""
        self.tries += 1
        cursor.execute("SELECT nom, value FROM Calendrier")
        LIST = cursor.fetchall()
        for t_uplet in LIST:
            str_data = t_uplet[-1]
            nom = t_uplet[0]
            # /str_data/ is a string of the dict /data/ (result of <str(data)>). 
            # It needs to be converted before check_date can be applied
            data = str_to_dict(str_data)
            T = check_date(nom, data)
            if T:
                break
        if not T:
            return None
        else:
            say(T)

    def run(self, l=None):
        self.test()

    def __str__(self):
        return "L'agenda intégré par défaut"


class Start_Background(threading.Thread):

    def __init__(self):
        global working
        threading.Thread.__init__(self)
        self.protocoles = []
        standard = [{"tries": 0, "executions": 0, "cmd": "", "condition": 'result = True '}, Agenda_prot()]
        try:
            file = open("{}/training_log/protocols.trn".format(folder), 'rb')
            assert os.path.getsize("{}/training_log/protocols.trn".format(folder)) > 0, ""
        except:
            file = open("{}/training_log/protocols.trn".format(folder), 'xb')
            pickle.dump(standard, file)
            file.close()
            self = Start_Background()
            return None
        proto = pickle.load(file)
        for item in proto:
            if item.__class__.__name__ == "agenda_prot":
                1 + 1
            else:
                self.protocoles.append(Protocoles(load=item))

    def run(self):
        """overwriten event that allows for checking of mutliple threads"""
        global working
        working = True
        time.sleep(1)
        while working:
            for protocole in self.protocoles:
                protocole.test()
            time.sleep(1.5)
        self.store()

    def add_protocol(self, cmd, condition):
        """adds a protocol to the background"""
        prot = Protocoles(cmd, condition, None)
        self.protocoles.append(prot)

    def store(self):
        file = open("{}/training_log/protocols.trn".format(folder), 'wb')
        memoire = [prot.store() for prot in self.protocoles]
        pickle.dump(memoire, file)
        file.close()


def add_protocole(Background_proccess):
    """Définis et ajoute un protocole au processus de fond"""
    cmd = ask("Quelle est la commande du processus?")
    C = teste_code(cmd)
    if C:
        if C == True:
            say("Compris", 1)
        else:  # la commande doitse voir ajouter
            cmd = 'result = ' + cmd
            say("Compris", 1)
    else:
        raise Exception("La commande n'est pas acceptable.")
    condition = ask("Quel est le code de lancement du protocole ?")
    C = teste_code(condition)
    if not C:
        raise Exception("La condition n'est pas acceptable.")
    else:
        if C == True:
            say("Compris", 1)
        else:  # la commande doitse voir ajouter
            cmd = 'result = ' + cmd
            say("Compris", 1)
    Background_process.add_protocol(cmd, condition)


## miscelanious
def self_study():
    """Renvoie un diciotnnaire avec des informations de déboguage"""
    import socket
    reponse = {}
    reponse["reason"] = "new_connection"
    reponse["adress"] = folder + '/SARA 1.py'
    reponse["support"] = socket.gethostname()
    reponse["integrity_check"] = socket.os.chdir(folder)
    return reponse


def rechecher_sur_google(recherche):
    """Effectue la vraie recherche sur google de /recherche/"""
    import webbrowser
    webbrowser.open("https://www.google.fr/search?hl=fr&q={}".format(recherche.replace(' ', '+')))


## fonctions d'interraction

def couper_(sentence, coupeurs):
    """Coupe la phrase selon les coupeurs
    coupeurs = [coupeur1, coupeur2, coupeur3]  --> reponse = {0: part1, 1: part2, 2: part3 ...}
    où les parts sont des bouts de phrase (str)
    et les coupeurs sont des strings ou des listes"""

    def listifie(groupe):
        if type(groupe) == type(list()):
            return groupe[:]
        else:
            return [groupe]

    def distance_groupe(groupe1, groupe2):
        """Renvoie la distance entre groupe1 et groupe 2 ou groupe1 est une str.split() et groupe2 aussi"""
        dist = 0
        for i in range(min(len(groupe1), len(groupe2))):
            dist += distance_mot(groupe1[i], groupe2[i])
        return dist

    ## détection des points de coupe
    # print(len(coupeurs),'coupeurs')
    phrase = sentence.split()
    # print(sentence,' ==> ',  phrase)
    R = {}  # stockage des id des coupeurs
    for indexe in range(len(coupeurs)):
        coupeur = coupeurs[indexe]
        c = listifie(coupeur)
        min_min = 5
        l = -indexe
        m = 1
        for marque in c:
            n = len(marque.split())
            min_dist = 5
            # print("\t",len(phrase),n)
            j = l
            for k in range(len(phrase) - n + 1):
                g1 = phrase[k:k + n]
                g2 = marque.split()
                dist = distance_groupe(g1, g2)
                # print(j,k)
                # prise du minimum des mots
                if min_dist >= dist / n:
                    # print(g1,g2, dist/n)
                    j = k
                    min_dist = dist / n
            # prise du minimum des marques
            if min_min / m >= min_dist:
                l = j
                m = n
                min_min = min_dist * n
        # ajout dans la réponse
        R[l] = (l + m, indexe)  # tq phrase[l,R[l][0]] soit le coupeur et R[l][1] soit l'indexe du coupeur
    ## coupure
    reponse = {}
    L = list(R.keys())
    L.sort()
    # print(R,L)
    for i in range(len(L) - 1):
        debut = R[L[i]][0]  # la fin de ce coupeur
        fin = L[i + 1]  # le début du prochain coupeur
        # print(debut,fin)
        reponse[R[L[i]][1]] = phrase[debut:fin]
    reponse[R[L[-1]][1]] = phrase[R[L[-1]][0]:]
    # print(reponse)
    ## finalisation
    for i in reponse.keys():
        if reponse[i] == [] and i == coupeurs[-1]:
            reponse[i] = ""
        else:
            t = ''
            for mot in reponse[i]:
                t += mot
                t += ' '
            reponse[i] = t[:-1]
    print(reponse)
    return reponse


def definir(contexte):
    """définit un mot. Permet également de créer un répertoire"""
    request = contexte["requête"]
    # request est un split, donc il faut l'unir
    t = ''
    for r in request:
        t += (str.lower(r) + ' ')
    T = t[:-1]
    # T est notre phrase de requête sous forme <str>
    coupeurs = [["définir", "déterminer"], ["comme", "en tant que", "à l'instar", "pour",
                                            'en tant que synonyme de', 'comme synonyme de', "pour synonyme de"]]
    connection = ["significance", "mot"]
    D = couper_(T, coupeurs)
    comme = D[1]
    a_def = D[0]

    threshold = lambda n: 2 + 0.5 * sqrt(n) * log(1 + (n / 10))

    rep = ["répertoire", "agenda", "almanach", "barème", "bordereau", "cahier", "calepin", "catalogue", "classement",
           "classeur", "dénombrement", "digeste", "directory", "dossier", "fichier", "index", "inventaire", "kyrielle",
           "liste"
           "mémoire", "nomenclature", "recueil", "registre", "relevé", "série", "sommaire", "suite", "table"]
    if not comme:
        comme = ask("Quelle est la nature de {} ?".format(a_def), hover="Parmis répertoire")

    if min([distance_mot(comme.split()[0], rep[i]) for i in range(len(rep))]) < threshold(len(comme.split()[0])):
        if positif(ask("Créer le nouveau répertoire dans la mémoire : {} ?".format(a_def),
                       hover="Ceci rajoutera en mémoire une table de donnée dans laquelle vous pourrez rajouter des informations. Des données additionnelles peuvent être demandées")):
            create_table(a_def)
    else:
        add_significance(comme, a_def)


def rappeler(context):
    """Rappelle une date"""
    request = context["requête"]
    # request est un split, donc il faut l'unir
    t = ''
    for r in request:
        t += (str.lower(r) + ' ')
    T = t[:-1]
    # T est notre phrase de requête sous forme <str>
    coupeurs = [["Rappelle moi", "Rappelle-moi"], ["le", "au jour du"], ["dans"], ["tous les", "avec une fréquence de"]]
    D = couper_(T, coupeurs)
    reason = "Rajouté par SARA"
    nom = D[0]
    date = D[1]
    espacement = D[2]
    freq = D[3]
    # récupération de la date
    if not date and espacement:
        date = decaller_date(today(), espacement)
    elif not date and not espacement:
        date = ask("Quand est-ce que ce rappel doit être opéré?", hover='Sous la forme AAAA-MM-JJ (HH:MM:SS)')
    try:
        to_datetime(date)
    except:
        try:
            to_datetime(date, True)
        except:
            # si le format ne correspond pas
            # on suppose le format est dd/mm/yyyy
            L = date.split("/ ")
            dd = L[0]
            mm = L[1]
            yy = L[2]
            if len(yy) == 2:
                yy = '20' + yy
            if not str.isnumeric(mm):
                M = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
                i = id_list(mm.lower(), M)
                if i < 10:
                    mm = "0" + str(i)
                else:
                    mm = str(i)
            date = yy + '-' + mm + '-' + dd
    if not freq:
        freq = None
    if positif(ask("Voulez-vous customiser le message qui sera alors donné?")):
        message = ask("Quel message doit-on alors donner?")
    else:
        message = None
    try:
        add_date(date, reason, message, freq=freq)
    except:
        say("Une erreur s'est produite.")
        if freq:
            if positif(ask("Avez-vous bien donner une fréquence?")):
                freq = ask("Pouvez-vous alors la répéter svp?")
            else:
                say("D'accord. j'en avais détecté une, ça doit être pour ça.")
                freq = None
        else:
            say("Merci de réessayer")
        add_date(date, reason, message, freq=freq)


def ajout(context):
    """Ajoute [information] à [source]"""
    request = context["requête"]
    # request est un split, donc il faut l'unir
    t = ''
    for r in request:
        t += (str.lower(r) + ' ')
    T = t[:-1]
    # T est notre phrase de requête sous forme <str>
    vb_search = ["Ajouter", "Mémoriser", "Mettre", "Stocke", "Enregistre", "Sauvegarder", "retenir"]
    va_search = ["va " + vb for vb in vb_search]
    C1 = vb_search + va_search
    coupeurs = [C1, ["à", "au", "dans", "à destination de", "vers", "au dossier"]]
    D = couper_(T, coupeurs)
    information = D[0]
    destination = D[1]
    if not destination:
        destination = "blabla"
        if positif(ask("Voulez-vous rajouter une information?")):
            value = ask("Que rajouter?")
        else:
            value = None
    else:
        if positif(ask("Voulez-vous rajouter une information?")):
            value = ask("Que rajouter?")
        else:
            value = None
    place(destination, information, value)


def execute(context):
    """Exécute le protocole"""
    ensemble_protocoles = BackGround.protocoles
    ## foncitonnement normal
    request = context["requête"]
    # request est un split, donc il faut l'unir
    t = ''
    for r in request:
        t += (str.lower(r) + ' ')
    T = t[:-1]
    # T est notre phrase de requête sous forme <str>
    vb_search = ["Exécuter", "Accomplir", "Effectuer", "Réaliser", "Faire"]
    va_search = ["va " + vb for vb in vb_search]
    C1 = vb_search + va_search
    coupeurs = [C1, ["le protocole", "la commande"]]
    D = couper_(T, coupeurs)
    prot1 = D[0]
    prot2 = D[1]
    if not prot1:
        prot1 = prot2
    # find the closest protocole name to prot1
    min_dist = 5
    i = -1
    for j in range(len(ensemble_protocoles)):
        name = ensemble_protocoles[j].name
        dist = distance_mot(prot1, name)
        if dist < min_dist:
            min_dist = dist
            i = j
    if i == -1:
        say("Aucun protocole avec le nom {} n'a été trouvé, merci de réessayer".format(prot1),
            hover="Vos options sont {}".format(ensembles_protocoles))
    ensemble_protocoles[j].run()


def cree_protocole(context):
    """Crée un protocole"""
    cmd = ask("Quelle commande dois-je exécuter?")
    condition = ask("Quand est-ce que ce protocole doit-être activé ?")
    BackGround.add_protocol(cmd, condition)


def donner(context, confirm=True):
    """Renvoie [information] de [source]
    Affiche le résultat"""
    ## foncitonnement normal
    ## > lecture de la demande
    request = context["requête"]
    # request est un split, donc il faut l'unir
    t = ''
    for r in request:
        t += (str.lower(r) + ' ')
    T = t[:-1]
    # T est notre phrase de requête sous forme <str>
    vb_search = ["Renvoyer", "Rappeler", "Donner", "Trouver"]
    va_search = ["va " + vb for vb in vb_search]
    vm_search = [vb + " moi" for vb in va_search + vb_search]
    vm_search += [vb + "-moi" for vb in va_search + vb_search]
    C1 = vb_search + va_search + vm_search
    coupeurs = [C1, ["à partir de", "depuis le", "rangée dans le dossier", "rangée dans", "du dossier"]]
    D = couper_(T, coupeurs)
    destination = D[1]
    information = D[0]
    ## > récupération de l'information
    print(destination, information)
    if not destination:
        if fits(information, ensemble_des_tables()):  # si l'information est une table
            destination = information
            information = None
        else:
            destination = "blabla"
    if not information:
        information = None
    print(destination, information)
    C = fetch(destination, information)
    if len(C) <= 1:
        if not C:
            say("Aucun élément trouvé", hover="Recherche effectuée dans {}".format(closest_table(destination)))
        else:  # C = [rep]
            say("{} renvois {}".format(information, C[0]))
    else:
        assert len(C) >= 2, "Unexpected State"
        say("Plusieurs informations ont étés trouvées, et seront donc afficher dans DATA.")
        if positif(ask("Confirmer la demande ?")):
            ## affichage dans DATA
            def remake(self, confirm=True):
                """Ends and restarts the Canvas"""
                if confirm:
                    if not positif(ask("Voulez-vous sortir de ce mode d'affichage?")):
                        return None
                global Info
                Info.destroy()
                Info = Canvas(DATA, bg='azure', width=700, height=700)
                Info.pack(side=TOP)

            def Rclick(self, event):
                y = event.y
                if y < 300:
                    self.up(event)
                elif y > 400:
                    self.down(event)
                else:
                    self.remake()

            def disp(self):
                Info.delete("all")
                for i in range(min(6, N - n)):
                    Info.create_text(x=10, y=50 + 100 * i, text=str(C[n + i]))

            def down(self, event):
                self.n += 1
                if self.n >= self.N:
                    self.n = 0
                disp()

            def up(self, event):
                self.n -= 1
                if self.n < 0:
                    self.n = self.N
                disp()

            def LClick(self, event):
                y = event.y
                i = abs(y // 100)
                i = min(6, i)
                truc = self.C[i + self.n]
                say(str(truc))

            def __init__(self, C):
                global Info
                self.N = len(C)  # le nombre d'information trouvées
                self.n = 0
                self.C = C
                remake(False)
                Info.bind("<ButtonRelease-1>", self.LClick)
                Info.bind("<ButtonRelease-2>", self.Rclick)
                Info.bind("<Prior>", self.up)
                Info.bind("<Next>", self.down)
                Info.bind("<Escape>", lambda e: self.remake())
                Info.bind("<Return>", lambda e: self.remake())
                say("Affichage_complet", hover='LeftClick for more Info, Right Click to move')

            A = affichage(C)
            A.disp()
        else:
            say("Ok")
    return None


def checklist(context):
    context["requête"] = "Trouve depuis"
    donner(context, confirm=False)


def supprime(context):
    request = context["requête"]
    # request est un split, donc il faut l'unir
    t = ''
    for r in request:
        t += (str.lower(r) + ' ')
    T = t[:-1]
    # T est notre phrase de requête sous forme <str>
    vb_search = ["Supprimer", "Enlever", "Oublier", "Retirer", "Effacer"]
    va_search = ["va " + vb for vb in vb_search]
    C1 = vb_search + va_search
    coupeurs = [C1, ["de", "dans", "à partir de", "depuis", "rangée dans le dossier", "rangée dans",
                     "du dossier", "le dossier"]]
    D = couper_(T, coupeurs)
    information = D[0]
    destination = D[1]
    # cas supprime le dossier [info]
    if not information:
        information = destination
        destination = None
    # cas où on exprime la destination
    if destination:
        pull(destination, information)
    # sinon.
    else:
        if information in ensemble_des_tables():
            destination = information
            delete_table(destination)
        else:
            dest = closest_table(information)
            say("{} ne semble pas être une table connue.".format(scrub(information)))
            if positif(ask("Pensiez-vous à {} ?").format(dest)):
                delete_table(dest)
            else:
                if not positif(ask("Est-ce que {} est dans la table par défaut?", hover=
                "Ceci peut se produire si il s'agit d'un élement dont l'adresse d'écriture n'a pas été spécifiée")):
                    say("Je ne sais que faire...")
                    return None
                else:
                    pull("blabla", information)


## algorithme

# chargement de l'abre principal
forest.append(Arbre(address='principal'))


# chargement de l'affichage

def QUID():
    say("L'aide n'est pas complète", hover="merci de me dire de la finaliser")
    say("...")
    say("SARA1 est un arbre décisionnel qui compare chaque node a une commande de l'utilisateur,\navant de trouver une action finalisant cette demande et ainsi résolvant la question.")
    say("Cependant, là où l'algorithme devient intelligent, c'est en sa capacité d'apprendre.\nEn effet, SARA est capable de retenir quelles actions doivent avoir quelles conséquences,\net peut donc s'améliorer dans le futur.",
        hover="N'est pas présentement intégré.")
    say("Des astuces sont disponibles un peu de partout (même dans les boites de dialogues)\nen passant la souris dessus. Elles devraient vous permettre de mieux vous repérer.")
    say("La partie de l'écran 'data' est interractive. Un click simple vous pemet de déveloper\nune node, et ainsi de gagner accés à plus d'information, tandis qu'un clic double permet\nde créer une nouvelle node",
        hover="cette partie s'active aprés la première interraction avec l'utilisateur")
    say("Il n'est pas recommandé pour les béta-testeurs de créer leurs nodes.")
    say("SLEEP MODE IS IN AN EXPERIMENTAL STATE. ATTEMPTING IT MIGHT ENDANGER THE INTEGRITY OF THE CURRENT PROGRAM")
    say("L'éran de DATA vous donne également des nombres. Il s'agit de l'incentive.\nL'incentive correspond à l'envie que SARA a de répondre considérer\ncette node dans son procéssus décisionnel.")


class CreateToolTip(object):
    """
    create a tooltip for a given widget
    CREDIT IS DUE TO Stevoisiak (https://stackoverflow.com/users/3357935/stevoisiak) FOR THIS MODULE.
    """

    def __init__(self, widget, text='widget info'):
        self.waittime = 500  # miliseconds
        self.wraplength = 180  # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = Label(self.tw, text=self.text, justify='left',
                      background="#ffffff", relief='solid', borderwidth=1,
                      wraplength=self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


def link_to_key(widget, key):
    """activates the button command when key is pressed"""
    fen.bind(key, lambda event: widget.invoke())


def QUIT():
    global fen_opened
    global working
    global discussion_records
    pickle.dump(discussion_records, (open(folder + '/training_log/records.trn', 'wb')))
    working = False
    DEMAND.set("INTERRUPT")
    say("au revoir")
    for tree in forest:
        tree.store()
    fen.destroy()
    fen_opened = False


fen_opened = True  # mémorise si la fenêtre est ouverte ou ou non
fen = Tk()
TOP_fen = Frame(fen, bg="white")
TOP_fen.pack(side=TOP)
Quitter = Button(TOP_fen, text='QUITTER', command=QUIT, bg="ghost white")
Quitter.pack(side=LEFT)
Sleep = Button(TOP_fen, text="Sommeil", command=sleep, bg="ghost white")
Sleep.pack(side=LEFT, padx=1)
HELP = Button(TOP_fen, bitmap='question', command=QUID, bg="cyan", fg='blue')
HELP.pack(side=RIGHT)
WIN = Frame(fen, bg='white')
DATA = Frame(fen, bg='white')
WIN.pack(side=LEFT, padx=2)
DATA.pack(side=RIGHT, padx=2)
Canvas(fen, bg='black', width=3, height=730, border=0).pack(side=RIGHT)  # séparateur

Data_label = Label(DATA, text='DATA', bg='light sea green', fg='white')  # titre
Data_label.pack(side=TOP)
Win_label = Label(WIN, text='Interaction', bg='light sea green', fg='white')  # titre
Win_label.pack(anchor='n')
talk_bar = Frame(WIN, borderwidth=0, bg='grey2', width=60)
talk_bar.pack(side=BOTTOM)
DEMAND = StringVar()
IMMEDIATE = StringVar()
T_FIELD = Entry(talk_bar, width=60, textvariable=IMMEDIATE, bg='linen', fg='maroon', borderwidth=1)  # talking field
T_FIELD.pack(side=LEFT, pady=3)
fen.title('SARA')
fen.configure(bg='white')

SAY = Button(talk_bar, command=SARA_input, bitmap='questhead', bg='linen', fg='maroon')
SAY.pack(side=LEFT)

Info = Canvas(DATA, bg='azure', width=700, height=700)
Info.pack(side=TOP)


def encadre(texte, x, y, widget=Info, size=12, color='purple', text_color=None, indice=None, indice_color="black"):
    """Encadré du texte de la couleur color centré sur le point x,y"""
    if text_color == None:
        text_color = color
    texte = str(texte)
    l = len(texte)
    widget.create_text(x, y, text=texte, font=('helvetica', str(size)), fill=text_color)
    w = l * size * 2 / 3
    h = 2 * size
    points = [[x - w / 2 - h / 2, y], [x - w / 2, y - h / 2], [x + w / 2, y - h / 2], [x + w / 2 + h / 2, y],
              [x + w / 2, y + h / 2], [x - w / 2, y + h / 2]]
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[i - 1]
        widget.create_line(x1, y1, x2, y2, fill=color)
    if indice == None:
        return None
    else:
        encadre(indice, x + h / 2 + w / 2, y - h / 2, widget=widget, size=(2 * size) // 3, color=indice_color)


# Ergonomie
CreateToolTip(Quitter, "Sauvegarde et ferme le processus (ESCAPE)")
CreateToolTip(SAY, "Valider (ENTER)")
CreateToolTip(T_FIELD, "Parlez ici à SARA!")
CreateToolTip(Data_label, "Affiche la réflexion menant au résultat")
CreateToolTip(HELP, "Aide et explications (F1)")
CreateToolTip(Win_label, "Affiche la conversation avec SARA.")
CreateToolTip(Sleep, "Désactive SARA temporairement et la laisse apprendre (F5)")
link_to_key(Sleep, "<F5>")
link_to_key(SAY, '<Return>')
link_to_key(Quitter, "<Escape>")
link_to_key(HELP, "<F1>")
T_FIELD.focus_set()

fen.iconbitmap(folder + '\\sara_1_icon.ico')
# fen.tk.call("wm","iconbitmap",fen._w,PhotoImage(folder + '/SARA 1 icon.png',master = fen))

# remember activation
if 'logins' in global_vars:
    connections = global_vars["logins"]
    last_connection = connections[-1]
else:
    connections = [{"date": today(), "additionnal_context": {"reason": 'first_connection_double'}}]
    global_vars["logins"] = connections
    last_connection = today()
connections.append({"date": today(), "additionnal_context": self_study()})
# start a background
BackGround = Start_Background()
BackGround.start()

# activation
fen.mainloop()
DEMAND.set("INTERRUPT")
# sauvegarde
print("do not leave, we are saving the last few things")
pickle.dump(discussion_records, (open(folder + '/training_log/records.trn', 'wb')))
for tree in forest:
    tree.store()
print("goodbye")
fen_opened = False
working = False
pickle.dump(global_vars, open(folder + "/global_vars.sara", 'wb'))
