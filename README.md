# Portage du CESM sur Lemaitre4

> **Auteur :** Louis Cleen  
> **Email :** louis.cleen@gmail.com  


## Table des matières

- [Introduction](#introduction)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Run compset X](#run-compset-x)
- [Run compset F2000climo](#run-compset-f2000climo)
- [Run compset B2000](#run-compset-b2000)
- [Exécution](#exécution)

## Introduction

Ce guide est dédié au **portage** du **CESM** ([Community Earth System Model](https://www.cesm.ucar.edu/models/cesm2 "NCAR - CESM2")) sur le cluster **Lemaitre4**, un cluster massivement parallèle du CÉCI ([Consortium des Équipements de Calcul Intensif](https://www.ceci-hpc.be/ "CÉCI")). Son contenu peut également servir de base pour porter le modèle sur d'autres clusters. 

En particulier, le **CESM 2.1.5** sera installé. Pour porter une version plus récente du modèle (2.2 ou bientôt 3.0), la marche à suivre peut différer et s’avérer potentiellement plus simple, car les dépendances requises sont alors plus récentes et donc plus susceptibles d’être disponibles sur la machine. 

Il faut savoir que le portage proposé ici reste local. Le modèle, les fichiers de configuration (compilateur, scheduler, etc.), certaines dépendances manquantes et toutes les données d'input sont téléchargés dans le répertoire personnel sur le cluster. L'idéal serait de contacter un administrateur du CÉCI pour installer les dépendances à l'échelle globale et de pouvoir partager les données d'input (le modèle est conçu pour permettre cela). Pour donner une idée, le dossier "inputdata" pour ce guide fait environ 13G et une simulation d'une année avec CAM et océan prescrit (résolution f19_f19_mg17) pèse 3,8G, mais ce poids dépend fortement des variables que l'on souhaite enregistrer et de la fréquence (journalière au lieu d'une moyenne mensuelle par exemple). 

**Note 1 :**  Le portage n'est nécessaire que sur les machines qui ne sont pas supportées (voir https://docs.cesm.ucar.edu/models/cesm2/config/2.1.5/machines.html). En pratique, très peu le sont. En Belgique, aucun calculateur n'est supporté. Cependant, j'ai pu remarquer que la VUB, l'équivalent du CÉCI en région flamande, avait porté le modèle sur au moins un de leurs clusters (voir https://hpc.vub.be/docs/software/usecases/ et https://github.com/vub-hpc/cesm-config). 

**Note 2 :** Un vrai portage se termine par des tests de validation. Aucun n'a été réalisé ici car le but était de montrer la faisabilité, et non de produire et publier des résultats scientifiques. 


## Prérequis
- Vocabulaire lié au CESM (component, case, compset, resolution, etc.) 
- Accès au cluster Lemaitre4 (CÉCI)
- Connaissances basiques en calcul haute performance (HPC)  

Comprendre le fonctionnement d'un modèle de circulation générale est utile pour exploiter le modèle mais ce n'est pas indispensable pour ce guide. Concernant les deux derniers points, la documentation du CÉCI (https://support.ceci-hpc.be/doc/) est un excellent point de départ et est très accessible. 

### Liens utiles
#### Ressources :
- [CESM dépôt GitHub](https://github.com/ESCOMP/CESM)
- [Lien NCAR du modèle](https://www.cesm.ucar.edu/models/cesm2) 
- [Component Sets](https://docs.cesm.ucar.edu/models/cesm2/config/2.1.5/compsets.html)
- [Grid Resolution](https://docs.cesm.ucar.edu/models/cesm2/config/2.1.5/grids.html)
- [CÉCI Tier-2 Clusters](https://www.ceci-hpc.be/clusters/) 

#### Tutorials :
Le NCAR propose chaque année un tutoriel (liste [ici](https://www.cesm.ucar.edu/events/tutorials)). Dans chaque tutoriel, une section "agenda" permet de retrouver l'ordre des présentations (utile pour trouver le replay correspondant sur YouTube) et parfois les fichiers .pdf des présentations sont également disponibles. Sur la chaîne YouTube du NCAR, on retrouve différentes playlists par année (exemple : [2025](https://www.youtube.com/playlist?list=PLsqhY3nFckOHvxlfFk9dG7e9fD-_GOXeH) et [2024](https://www.youtube.com/playlist?list=PLsqhY3nFckOFIONRpwgd3pvyGuSBYvqqR)). Concernant le portage et l'utilisation du modèle, les tutoriels des années < 2023 semblent plus complets.

#### Documentations
Pour comprendre comment utiliser le modèle, j'ai essentiellement utilisé cette documentation :
https://ncar.github.io/CESM-Tutorial/README.html  
Cependant, j'ai remarqué que la page a beaucoup évolué (plusieurs sections semblent avoir été ajoutées), elle repose maintenant sur CESM 3.0, qui sera utilisé pour le tutoriel 2026. 
- [CESM2.1 Quickstart Guide](https://escomp.github.io/CESM/versions/cesm2.1/html/)
- [CIME documentation](https://esmci.github.io/cime/versions/master/html/index.html)  


## Installation
L'objectif est de porter le CESM2 sur Lemaitre4. Pour travailler proprement, la structure utilisée sera la suivante : le modèle et les cases (scénarios simulés, c.-à-d. choix de la résolution, des paramètres d'intérêt etc.) seront dans le répertoire `"$HOME"` et les données d'input ainsi que la sortie du modèle seront dans le répertoire `$GLOBALSCRATCH`. Le répertoire dit "scratch" est beaucoup plus rapide pour les opérations I/O et est adapté pour stocker de grosses quantités de données. Cependant, ce dernier est généralement vidé une fois par an.

### Télécharger le modèle

Pour commencer, il faut télécharger le modèle. Plus particulièrement nous utiliserons **CESM 2.1.5**, une version stable et largement utilisée. Ce choix est cohérent avec le dernier rapport du GIEC (AR6), qui s'appuie sur les simulations CMIP6. Pour CESM, ces simulations ont été produites avec la branche CESM2.1, dont la version 2.1.5 est une évolution de maintenance.

Il est important de comprendre que le dépôt GitHub ne contient pas tout le code, mais plutôt des scripts permettant de télécharger tout le nécessaire via Subversion (svn) qui est un outil de gestion de versions comme Git. Cette dépendance peut être un problème, car certains clusters ne l'ont pas. Notez que les versions plus récentes du CESM n'utilisent plus svn.

Dans le répertoire 'HOME' :  
```bash
mkdir CESM
cd CESM
git clone --branch release-cesm2.1.5 https://github.com/ESCOMP/CESM.git release-cesm2.1.5
cd release-cesm2.1.5
git describe --tags --exact-match
```

La dernière commande doit afficher exactement `release-cesm2.1.5`. Si ce n'est pas le cas (ou tout simplement pour changer de tag ou branche), on utilise `git checkout`. 

Ensuite il faut récupérer tous les composants du modèle. Pour cela, il faut lancer le script `checkout_externals` depuis la **racine** (ici depuis le dossier `release-cesm2.1.5`).  
Le script utilise **Subversion** (svn), il faut donc charger ce module au préalable. Avec la commande 'module spider Subversion', on peut voir (sur Lemaitre4), que le module est disponible dans la `toolchain releases/2023b`. Il faut donc faire :
```bash
ml releases/2023b
ml Subversion/1.14.2-GCCcore-13.2.0
```
---
**EDIT** : Je viens de remarquer que Subversion est maintenant disponible directement sans charger de module. Pour vérifier cela, faites
```bash
which svn
```
Un complément d'information est donnée à la fin pour expliquer comment se passer de svn (en particulier pour télécharger les données d'input).  

---  

Nous pouvons maintenant récupérer les composants avec :
```bash
./manage_externals/checkout_externals
```


Ensuite, nous créons le dossier qui contiendra tous nos futurs cases (scénarios à simuler) : 
```bash
mkdir $HOME/CESM/case
``` 

En dernier lieu, il est possible que le modèle ait besoin de la structure complète prévue par `config_machines.xml`. Il peut donc être nécessaire d'exécuter ceci :
```bash 
mkdir -p $GLOBALSCRATCH/cesm/{inputdata/atm/datm7,scratch,archive,cesm_baselines,tools/cprnc}
```
Notez que le dossier inputdata contiendra les données d'entrée du modèle, le dossier scratch sera le dossier de travail pendant une simulation, et le dossier archive servira à stocker les sorties du modèle, une fois la simulation terminée.

### Installation des dépendances Perl
Certains composants ont besoin du module Perl XML::LibXML. Perl est bien présent, mais ce module, lui, ne l'est pas. Il va donc falloir l'installer localement.
```bash
module purge
ml releases/2023a
ml Perl-bundle-CPAN/5.36.1-GCCcore-12.3.0
ml libxml2/2.11.4-GCCcore-12.3.0 
```

Ensuite, vérifions que xml2-config est accessible
```bash
which xml2-config
xml2-config --version
```

Installation dans $HOME/perl5 (pas besoin de root)
```bash
cpanm --local-lib=$HOME/perl5 --force XML::LibXML
cpanm --local-lib=$HOME/perl5 --force XML::SAX
```

Pour vérifier que tout fonctionne, exécutez ces deux commandes :
```bash
export PERL5LIB="$HOME/perl5/lib/perl5/x86_64-linux-thread-multi:$HOME/perl5/lib/perl5"
perl -MXML::LibXML -e 'print "XML::LibXML version $XML::LibXML::VERSION\n"'
```
La dernière doit afficher `XML::LibXML version 2.X`. 

## Configuration
Plusieurs méthodes sont ensuite possibles pour porter le modèle. Le plus simple est de travailler localement en créant un dossier `.cime` à la racine du répertoire `$HOME`. Le modèle détectera automatiquement ce dossier et chargera les configurations qu'il contient.
```bash
mkdir $HOME/.cime
```

Note : pour voir les dossiers qui commencent par un point, il faut utiliser l'option `-a` avec `ls`, par exemple : `ls -la`

Ensuite dans ce dossier `.cime`, il faut ajouter 3 fichiers de configurations xml :
`config_machines.xml`, `config_batch.xml` et `config_compilers.xml`. Heureusement, vous n'aurez pas besoin de les créer, j'ai fait ce travail pour vous. Ils se trouvent directement dans ce dépôt GitHub. Vous devriez obtenir :
```text
~/.cime/                 
├── config_machines.xml
├── config_compilers.xml
└── config_batch.xml
```

**Note :** Les configurations sont lues dans cet ordre : `~/.cime/` d'abord, puis celles par défaut. Donc nos configurations surchargent celles situées dans le code téléchargé (`release-cesm2.1.5/cime/config/cesm/`).




Le premier sert à définir les caractéristiques physiques et matérielles de la machine (architecture des processeurs, nombre de coeurs par node etc.).  
Le deuxième fichier définit comment soumettre les jobs au gestionnaire de files d'attente de la machine, c'est à dire au scheduler (en l'occurrence SLURM sur Lemaitre4). Il faut comprendre que le CESM soumet lui-même le(s) job(s) de la simulation. Habituellement, on crée un script avec des commandes pour le scheduler, ici c'est directement le modèle qui crée les scripts dont il a besoin. Donc par exemple, si l'on souhaite recevoir un mail chaque fois que le scheduler démarre ou arrête notre job, on peut ajouter après la ligne 51 :
```xml
<directive>--mail-user=votre_adresse_mail</directive> 
<directive>--mail-type=ALL</directive>
```

Le troisième fichier concerne les instructions de compilation (en particulier concernant le code source Fortran).


### Pour information :
Concevoir ces trois fichiers représente de loin la partie la plus complexe. Le plus simple est de s’inspirer de configurations déjà existantes, par exemple dans le dossier `cime/config`, à la racine du code. Ensuite, un procédé itératif commence où, par essais-erreurs, on essaye de compiler, on regarde ce qui ne va pas, on modifie un des fichiers de configuration et on répète (sans savoir si on est proche du but).

Pour être totalement transparent, n’étant pas un expert en HPC, l’intelligence artificielle m’a été d’une aide précieuse dans cette tâche. Plus précisément, voici, à titre d’information, comment j’ai procédé :  
J’ai utilisé Claude Opus 4.7 et j’ai travaillé fichier par fichier. Pour ce faire, je lui ai fourni un template de la structure du fichier ainsi que comme exemple la configuration des machines supportées. Ensuite, Claude me donnait des commandes à exécuter pour identifier l’architecture du cluster, les modules disponibles, etc. Cela n’a évidemment pas fonctionné du premier coup, mais après quelques jours de travail, j’ai pu créer les trois fichiers nécessaires.





## Run compset X

Pour utiliser le modèle, il y a essentiellement 4 commandes à retenir :
```bash
./create_newcase
./case.setup
./case.build
./case.submit
```

Commençons par la première commande, qui permet de créer un case, c'est à dire un scénario que l'on souhaite simuler. Pour tester le portage, vérifier et valider que tout fonctionne, nous allons créer un scénario "vide". Nous allons utiliser à cette fin le script `create_newcase` situé dans le dossier `cime` du modèle (cd `$HOME/CESM/release-cesm2.1.5/cime/scripts/`).  
La plupart des scripts nécessitent Python et il est donc nécessaire de charger le module approprié. On pourrait être tenté de faire `module load Python`, mais ce serait trop simple. En effet, les scripts du CESM utilisent le module "imp", supprimé des versions récentes de Python. Il faut donc utiliser une ancienne version (< 3.12). Par exemple :
```bash
ml releases/2023b
ml Python/3.11.5-GCCcore-13.2.0
```

Ensuite, pour créer le case, nous utilisons :
```bash
./create_newcase --case ~/CESM/case/cesm_test_X --compset X --res f19_g17 --machine lemaitre4 --compiler intel --mpilib impi --run-unsupported
```
Cette commande va créer un dossier `cesm_test_X` dans le répertoire `case` dans lequel le scénario sera un **compset X**, c'est à dire un compset "dead" où tous les composants sont désactivés (seul le coupler CPL fonctionne). La résolution n'a pas d'utilité ici (mais reste obligatoire), on prend donc une résolution grossière 'f19_g17'. Il ne faut pas oublier de préciser la machine (le nom est dans la configuration `config_machines.xml`) et d'ajouter `--run-unsupported` car le compset et la résolution choisis ne font pas partie des configurations testées dans CESM. Plus d'info sur les compset et les résolutions [ici](#ressources-).


Ensuite, pour générer notammment les scripts de soumission pour le scheduler, nous utilisons la commande suivante :
```bash
./case.setup
```
Cela devrait être rapide et devrait vous afficher "`You can now run './preview_run' to get more info on how your case will be run`". Faisons cela,
```bash
./preview_run
```
En particulier, cette commande permet de voir à quoi ressemble la demande qui sera envoyée au gestionnaire SLURM. La sortie de la commande devrait afficher une section `CASE INFO:` et une section `BATCH INFO:`. Le contenu de la première informe, entre autres, sur le nombre de nodes qui seront réservés, et le nombre total de tasks. La seconde permet de voir combien de temps sera réservé pour le job `case.run` et le job `case.st_archive`.

> Le CESM crée deux scripts, le premier, `case.run`, est la simulation et le second, `case.st_archive`, est un script d'archivage. Ce dernier dépend du premier, il ne se lancera que lorsque `case.run` a terminé. Il sert en fait à regrouper proprement les sorties de la simulation. Pour ce faire, il crée un dossier du même nom que le case à l'emplacement `$GLOBALSCRATCH/cesm/archive/<casename>` et y place les résultats ainsi que les logs. Pendant la simulation, les logs sont consultables dans `$GLOBALSCRATCH/cesm/scratch/<casename>`.

Si `case.run` a planté, ou si pour une raison particulière `case.st_archive` ne se lance pas, les logs se trouveront dans le dossier du case dans `$GLOBALSCRATCH/cesm/archive/`.

On peut remarquer avec `./preview_run` que notre réservation est de 128 tasks sur 1 node (une node complète sur Lemaitre4) et que le temps maximum de `case.run` est de 48h. Cette dernière valeur correspond à la valeur maximale walltime dans la configuration `config_batch.xml`. 

Notez que pour afficher des paramètres spécifiques, on peut utiliser des requêtes xml. Le tableau suivant, reprend quelques commandes utile. Pour exécuter ces requêtes, il faut au préalable charger le module Python (< 3.12).

| Commande                                                     | Simulation                                                                                     |
|--------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| ./xmlquery NTASKS,MAX_TASKS_PER_NODE,MAX_MPITASKS_PER_NODE   | Nombre de tasks MPI par composant et limites par node.                                         |
| ./xmlquery NTHRDS                                            | Nombre de threads OpenMP par task MPI, pour chaque composant.                                  |
| ./xmlquery TOTALPES                                          | Nombre total de tâches MPI utilisées sur tous les composants.                                  |
| ./xmlquery JOB_QUEUE                                         | Partition SLURM utilisée (ex. `batch`).                                                        |
| ./xmlquery JOB_WALLCLOCK_TIME                                | Walltime SLURM demandé au format HH:MM:SS.                                                     |
| ./xmlquery STOP_OPTION,STOP_N,STOP_DATE                      | Durée simulée **par job** : unité, nombre d'unités, date d'arrêt éventuelle .                  |
| ./xmlquery REST_OPTION,REST_N                                | Unité et fréquence d'écriture des restarts (checkpoint).                                       |
| ./xmlquery RESUBMIT                                          | Nombre de fois où le job sera resoumis automatiquement après succès.                           |
| ./xmlquery CONTINUE_RUN                                      | `FALSE` : démarrage à froid (lit les conditions initiales) ;`TRUE` : reprise depuis un restart |


> Remarquez que le nombre de tasks total ne correspond pas à l'addition du nombre de tasks de chaque composant. Le coupleur orchestre leur exécution, et c'est généralement conseillé et plus performant de leur laisser cette liberté. Par conséquent, les composants peuvent fonctionner sur les mêmes cores (de manière séquentielle). Cela n'est pas à confondre avec le nombre de threads OpenMP (le nombre de processus sur un même core CPU). Concernant le CESM, il est souvent conseillé de garder un seul thread par task MPI.

> Les paramètres liés aux restarts (checkpoint) sont expliqués plus en détail à la fin de ce guide.


Pour ce simple test, nous n'avons pas besoin de beaucoup de ressources. Pour modifier un paramètre, il faut utiliser la commande `./xmlchange`. Modifions le nombre de tasks, le walltime ainsi que la durée simulée, que nous fixons à 1 jour :

```bash
./xmlchange NTASKS_ATM=24,NTASKS_LND=24,NTASKS_ICE=24,NTASKS_OCN=24,NTASKS_CPL=24,NTASKS_ROF=24,NTASKS_GLC=24,NTASKS_WAV=24,NTASKS_ESP=1
./xmlchange JOB_WALLCLOCK_TIME=00:15:00,REST_OPTION=never
./xmlchange STOP_OPTION=ndays,STOP_N=1
```


Ensuite, nous devons regénérer le setup. Puisqu'il avait déjà été créé, nous devons forcer le script à le recréer avec l'option `--reset` :
```bash
./case.setup --reset
```

Maintenant que tout est prêt, nous pouvons passer à la compilation avec la commande :
```bash
./case.build
```
**Note :** cela peut prendre plusieurs minutes (en particulier lorsque nous créerons des cases avec des vrais compset).

Si des paramètres ont été changés après la compilation, il peut être nécessaire de recompiler. Pour ce faire, il est impératif de réaliser un nettoyage avec `./case.build --clean-all` avant de recompiler.


Pour terminer, il ne reste plus qu'à soumettre le job au gestionnaire. Pour ce faire, utiliser :
```bash
./case.submit
```

> Pour rappel, si le gestionnaire est SLURM, vous pouvez voir l'état du job (après soumission) avec `squeue -u <user>`. Vous devriez voir deux jobs, un associé à `case.run` et un à `case.st_archive`. Pour annuler un job, utilisez `scancel <jobid>`.


Si vous souhaitez suivre la progression en temps réel, vous pouvez consulter les logs du coupler à l'emplacement "`$GLOBALSCRATCH/cesm/scratch/<casename>/run/cpl.log.*`"


Le schéma classique devrait ressembler à ceci : 


```text
create_newcase     # crée la case et les fichiers env_*.xml
    ↓
xmlchange          # modifie les variables CIME
    ↓
case.setup         # génère .case.run et env_mach_specific.xml
    ↓
case.build         # compile cesm.exe
    ↓
case.submit        # soumet à SLURM, qui lance .case.run
    ↓
.case.run          # charge modules, lance srun cesm.exe
    ↓
case.st_archive    # archive sorties 
    ↓
(éventuellement)   # resubmit auto
```


## Run compset F2000climo
[To be continued]

Passons aux choses sérieuses. Nous proposons ici de simuler 13 mois (1 an + 1 mois de spin-up) afin de valider le bon fonctionnement du modèle. Pour réaliser cela dans un temps raisonnable, nous utiliserons un compset basé sur l'année 2000, dans lequel l'océan est prescrit, tandis que les composantes CAM, CLM et MOSART restent actives. Nous enregistrerons notamment les précipitations ainsi que les vents à 850 hPa afin de mettre en évidence le cycle saisonnier de la circulation atmosphérique et des moussons.  

Plus spéficiquement, nous créeons un case avec le compset F2000 et la résolution f19_f19_mg17. Ainsi, la grille atm et la grille ocn sont la même. Le "m" devant "g17" signifie "masked", c'est typique des compsets où l'océan est prescrit car nous avons pas besoin d'une vraie grille océanique séparée puisqu'il n'y a pas de calculs océaniques.

```bash
./create_newcase --case ~/CESM/case/cesm_seasons_F \
    --compset F2000climo --res f19_f19_mg17 \
    --machine lemaitre4 --compiler intel --mpilib impi
```


Durée : 13 mois (1 mois jeté = spin-up, 12 mois gardés)
```bash
./xmlchange NTASKS_ATM=64,NTASKS_LND=64,NTASKS_ICE=64,NTASKS_OCN=64,NTASKS_CPL=64,NTASKS_ROF=64,NTASKS_GLC=64,NTASKS_WAV=64
./xmlchange STOP_OPTION=nmonths,STOP_N=13
./xmlchange JOB_WALLCLOCK_TIME=6:00:00 --subgroup case.run,
./xmlchange REST_OPTION=never
```

Les données d'input devraient représentées environ 13G.
```bash
./case.setup
./preview_run
./check_input_data --download
./case.build
```

Les paramètres et la fréquence de sortie du composant CAM se modifient dans le fichier `user_nl_cam` (voir l'exemple donné dans le dossier `case/cesm_seasons_F` du dépôt).

```text
! ===================================================================
! Output configuration: h0 monthly enriched + h1 daily for key fields
! ===================================================================
nhtfrq = 0, -24   ! h0 = monthly mean, h1 = daily mean
mfilt  = 1, 31    ! h0: 1 month/file, h1: 31 days/file

fincl1 = 'T', 'TS', 'TREFHT', 'PRECT', 'PRECC', 'PRECL', 'PSL', 'PS',
         'U:', 'U200', 'U850:', 'V:', 'V200:', 'V850:', 'OMEGA:', 'OMEGA500:', 'Z500:',
         'CLDTOT', 'CLDLOW', 'CLDMED', 'CLDHGH', 'Z3',
         'FLNT', 'FSNT', 'LHFLX', 'SHFLX'

fincl2 = 'TS', 'TREFHT', 'TREFHTMN', 'TREFHTMX', 'PRECT', 'PSL',
         'FSNS', 'FLNS', 'LHFLX', 'SHFLX'
```


Ensuite :

```bash
./case.setup --reset
./case.submit
```

Les données de sorties devraient représentées environ 3.2G.



## Run compset B2000
[To be continued]


---

---
### Complément d'information - Subversion (svn)
La commande `stat` indique que svn a été installé le 5 juin sur Lemaitre4. Il n'était pas disponible lorsque j'ai commencé à porter le CESM. Cela m'avait posé de gros problèmes puisque la toolchain utilisée pour compiler et exécuter le modèle est `release/2023a` et ne possède pas svn (qui était seulement inclus dans `releases/2023b`) et évidemment il n'est pas possible de charger deux toolchains différentes en même temps. Ce faisant, j'avais dû réaliser un script bash pour télécharger manuellement les données d'input. Si besoin, ce script est également dans le dépôt GitHub.