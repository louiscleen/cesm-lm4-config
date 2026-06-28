# Portage du CESM sur Lemaitre4

> **Auteur :** Louis Cleen  
> **Email :** louis.cleen@gmail.com  


## Table des matières

- [Introduction](#introduction)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Run](#run)
- [Exécution](#exécution)

## Introduction

Ce guide est dédié au **portage** du **CESM** ([Community Earth System Model](https://www.cesm.ucar.edu/models/cesm2 "NCAR - CESM2")) sur le cluster **Lemaitre4** du CÉCI ([Consortium des Équipements de Calcul Intensif](https://www.ceci-hpc.be/ "CÉCI")). Son contenu peut également servir de base pour porter le modèle sur d'autres clusters. Il n'a pas pour but d'expliquer l'utilisation du modèle (il ne nécessite néanmoins presque aucun prérequis).

En particulier, le **CESM 2.1.5** sera installé. Pour porter une version plus récente du modèle (2.2 ou bientôt 3.0), la marche à suivre peut différer et s’avérer potentiellement plus simple, car les dépendances requises sont alors plus récentes et donc plus susceptibles d’être disponibles sur la machine. 

Il faut savoir que le portage proposé ici reste locale. Le modèle, les fichiers de configurations (compilateur, scheduler, etc.), certaines dépendances manquantes et toutes les données d'input sont téléchargées dans le répertoire personnelle sur le cluster. L'idéal serait de contacter un administrateur du CÉCI pour installer les dépendances à l'échelle globale et de pouvoir partager les données d'input (le modèle est conçu pour permettre cela). Pour donner une idée, le dossier "inputdata" pour ce guide fait environ 13G et une simulation d'un année avec CAM et océan prescrit (résolution f19_f19_mg17) pèse 3,8G, mais ce poids dépend fortement des variables que l'on souhaite enregistrer et de la fréquence (journalière au lieu d'une moyenne mensuelle par exemple). 

**Note 1 :**  Le portage n'est nécessaire que sur les machines qui ne sont pas supportées (voir https://docs.cesm.ucar.edu/models/cesm2/config/2.1.5/machines.html). En pratique, très peu le sont. En Belgique, aucun calculateur n'est supporté. Cependant, j'ai pu remarqué que la VUB, l'équivalent du CÉCI en région flammande, avait porté le modèle sur au moins un de leur cluster (voir https://hpc.vub.be/docs/software/usecases/ et https://github.com/vub-hpc/cesm-config). 

**Note 2 :** Un vrai portage se termine par des test de validation. Aucun, n'a été réalisé ici car le but était de montrer la faisabilité, et non de produire et publier des résultats scientifiques. 


## Prérequis
- Vocabulaire lié au CESM (component, case, compset, resolution, etc.) 
- Accès au cluster Lemaitre4 (CÉCI)
- Connaissances basique en calcul haute performance (HPC)  

Comprendre le fonctionnement d'un modèle de circulation générale est utile pour exploiter le modèle mais ce n'est pas indispensable pour ce guide. Concernant les deux derniers points, la documentation du CÉCI (https://support.ceci-hpc.be/doc/) est un excellent point de départ et est très accessible. 

### Liens utiles
#### Ressources :
- [CESM dépôt GitHub](https://github.com/ESCOMP/CESM)
- [Lien NCAR du modèle](https://www.cesm.ucar.edu/models/cesm2) 
- [Component Sets](https://docs.cesm.ucar.edu/models/cesm2/config/2.1.5/compsets.html)
- [Grid Resolution](https://docs.cesm.ucar.edu/models/cesm2/config/2.1.5/grids.html)
- [CÉCI Tier-2 Clusters](https://www.ceci-hpc.be/clusters/) 

#### Tutorials :
Le NCAR propose chaque année un tutoriel (liste [ici](https://www.cesm.ucar.edu/events/tutorials)). Dans chaque tutoriel, une section "agenda" permet de retrouver l'ordre des présentations (utile pour pour trouver le replay correspond sur youtube) et parfois les fichiers .pdf des présentations sont également disponible. Sur la chaine youtube du NCAR, on retrouve différentes playlist par année (exemple: [2025](https://www.youtube.com/playlist?list=PLsqhY3nFckOHvxlfFk9dG7e9fD-_GOXeH) et [2024](https://www.youtube.com/playlist?list=PLsqhY3nFckOFIONRpwgd3pvyGuSBYvqqR)). Concernant le portage et l'utilisation du modèle, les tutoriels des années < 2023 semblent plus complet.

#### Documentations
Pour comprendre comment utiliser le modèle, j'ai essentiellement utilisé cette documentation :
https://ncar.github.io/CESM-Tutorial/README.html  
Cependant, j'ai remarqué que la page a beaucoup évoluée (plusieurs sections semblent avoir été ajoutées), elle repose maintenant sur CESM 3.0, qui sera utilisé pour le tutoriel 2026. 
- [CESM2.1 Quickstart Guide](https://escomp.github.io/CESM/versions/cesm2.1/html/)
- [CIME documentation](https://esmci.github.io/cime/versions/master/html/index.html)  


## Installation
L'objectif est de porter le CESM2 sur Lemaitre4. Pour travailler proprement, la structure utilisée sera la suivante : le modèle et les cases (scénarions simulés, c.-à-d. choix de la résolution, des paramètres d'intérêt etc.) seront dans le répertoire `"$HOME"` et les données d'input ainsi que la sortie du modèle seront dans le répertoire `$GLOBALSCRATCH`. Le répertoire dit "scratch" est beaucoup plus rapide pour les opérations I/O et est adapté pour stocker des grosses quantitées de données. Cependant, ce dernier est généralement vidé une fois par an.

### Télécharger le modèle

Pour commencer, il faut télécharger le modèle. Plus particulièrement nous utiliserons **CESM 2.1.5**, une version stable et largement utilisée. Ce choix est cohérent avec le dernier rapport du GIEC (AR6), qui s'appuie sur les simulations CMIP6. Pour CESM, ces simulations ont été produites avec la branche CESM2.1, dont la version 2.1.5 est une évolution de maintenance.

Il est important de comprendre que le dépôt GitHub ne contient pas tout le code, mais plutôt des scripts permettant de télécharger tout le nécessaire via Subversion (svn) qui est un outil de gestion de versions comme Git. Cette dépendance est un vrai problème, peu de personne l'utilise aujourd'hui, beaucoup de cluster ne l'ont pas. Les versions plus récentes du CESM n'utilisent plus SVN (FFFFFFFj'ai pris connaissance de cela tardivement).

Dans le répertoire 'HOME' :  
```bash
mkdir CESM
cd CESM
git clone --branch release-cesm2.1.5 https://github.com/ESCOMP/CESM.git release-cesm2.1.5
cd release-cesm2.1.5
git describe --tags --exact-match
```

La dernière commande doit afficher exactement `release-cesm2.1.5`. Si ce n'est pas le cas (ou tout simplement pour changer de tag ou branche), on utilise `git checkout`. 

Ensuite il faut récupérer tous les composants du modèle. Pour cela, il faut lancer le script `checkout_externals` depuis la **racine** (ici depuis dossier `release-cesm2.1.5`).  
Le script utilise **Subversion** (svn), il faut donc charger ce module au préalable. Avec la commande 'module spider Subversion', on peut voir (sur Lemaitre4), que le module est disponible dans la `toolchain releases/2023b`. Il faut donc faire :
```bash
ml releases/2023b
ml Subversion/1.14.2-GCCcore-13.2.0
```
---
**EDIT** : Je viens de remarquer que Subversion est maintenant disponible directement sans chargé de module. Pour vérifier cela, faite
```bash
which svn
```
Un complément d'information est donnée à la fin pour expliquer comment se passer de svn (en particulier pour télécharger les données d'input).  

---  

Nous pouvons mainetnant récupérer les composants avec :
```bash
./manage_externals/checkout_externals
```

En dernier lieu, créons le dossier qui contiendra tous nos futurs cases (scénarios à simuler) : 
```bash
mkdir $HOME/CESM/case
``` 

### Installation des dépendances Perl
Certains composants on besoin du module Perl XML::LibXML. Perl est bien bien présent, mais ce module, lui ne l'est pas. Il va donc falloir l'installer localement.
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
Plusieurs méthodes sont ensuite possible pour porter le modèle. Le plus simple est travailler localement en créant un dossier `.cime` à la racine du répertoire `$HOME`. Le modèle détectera automatiquement ce dossier et chargera les configurations qu'il contient.
```bash
mkdir $HOME/.cime
```

Note : pour voir les dossiers qui commencent par un point, il faut utiliser l'option `-a` avec `ls`, par exemple : `ls -la`

Ensuite dans ce dossier `.cime`, il faut ajouter 3 fichiers de configurations xml :
`config_machines.xml`, `config_batch.xml` et `config_compilers.xml`.

Heureusement, vous n'aurez pas besoin les créer, j'ai fait ce travail pour vous. Ils se trouvent directement dans ce dépôt GitHub.

Le premier sert à définir les caractéristiques physiques et matérielles de la machine (architecture des processeurs, nombre de coeurs par node etc.).  
Le deuxième fichier définit comment soumettre les jobs au gestionnaire de files d'attente de la machine, c'est à dire au scheduler (en l'occurence SLURM sur Lemaitre4). Il faut comprendre, que le CESM soumet lui même le(s) job de la simulation. Habituellement, on créer un script avec des commandes pour le scheluder, ici c'est directement le modèle qui crée les scripts qu'il a besoin. Donc par exemple, si l'on souhaite recevoir un mail chaque fois que le scheduler démarre ou arrêtre notre job, on peut ajouter après la ligne 51 :
```xml
<directive>--mail-user=votre_adresse_mail</directive> 
<directive>--mail-type=ALL</directive>
```

Le troisième fichier concerne les instructions de compilation (en particulier concernant le code source Fortran).










## Run de test

Pour utiliser le modèle, il y a essentiellement 3 commandes à retenir :
```bash
./create_newcase
./case.setup
./case.build
```

Commençons par la première commande, qui permet de créer un case, c'est à dire un scénario que l'on souhaite simuler. Pour tester le portage, vérifier et valider que tout fonctionne, nous allons créer un scénario "vide". Nous allons utiliser à cette fin le script le script `create_newcase` situé dans le dossier `cime` du modèle (cd `$HOME/CESM/release-cesm2.1.5/cime/scripts/`).  
La plupart des scripts nécessitent Python et il est donc nécessaire de charger le module approprié. On pourrait être tenter de faire `module load Python`, mais ce serait trop simple. En effet, les scripts du CESM utilisent le module "imp", supprimé des versions récente de Python. Il faut donc utiliser une ancienne version. Par exemple :
```bash
ml releases/2023b
ml Python/3.11.5-GCCcore-13.2.0
```

Ensuite, pour créer le case, nous utilisons :
```bash
./create_newcase --case ~/CESM/case/cesm_test_X --compset X --res f19_g17 --machine lemaitre4 --compiler intel --mpilib impi --run-unsupported
```
Cette commande va créer un dossier `cesm_test_X` dans le répertoire `case` dans lequel le scénario sera un **compset X**, c'est à dire un compset "dead" où touts les composants sont désactiver (seul le coupler CPL fonctionne). La résolution n'a pas d'utilité ici (mais reste obligatoire), on prend donc une résolution grossière 'f19_g17'. Il ne faut pas oublier de préciser la machine (le nom est dans la configuration `config_machines.xml`) et d'ajouter `--run-unsupported` car le compset et la résolution choisie ne font pas partie des configurations testé dans CESM. Plus d'info sur les compset et les résolutions [ici](#ressources-).


Avant d'aller plus loin, il est possible que le modèle ait besoin de la structure complète prévue par `config_machines.xml`. Il peut donc être nécessaire d'exécuter ceci :
```bash 
mkdir -p $GLOBALSCRATCH/cesm/{inputdata/atm/datm7,scratch,archive,cesm_baselines,tools/cprnc}
```






















Notez que ce portage utilise se base sur la toolchain releases/2023a de Lemaitre4 car certaines dépendances (ou certaines versions spécifique) n'étaients disponible que dans cette release. 


---
### Pour information :
Concevoir ces 3 fichiers représente de loin la partie la plus complexe. Le plus simple est de s'inspirer de fichiers déjà existant (par exemple dans le dossier cime/config à la racine du code). Ensuite, un procédé itératif commence où par essais erreur on essaye de compmiler, on regarde ce qui va pas, on modifie un des fichiers de configuration et on répète (sans savoir si on est proche du but). 
Pour être totalement transparent, n'étant pas un expert en HPC, l'intelligence artificelle fut une aide précieuse dans cette tâche. Plus spécifiquement, voici pour information comment fait :  
J'ai utilisé Claude Opus 4.7 et j'ai opéré fichier par fichier. Pour ce faire, je lui ait partagé un template de la structure du fichier et un ainsi que la configuration des machines supportés. Ensuite, Claude me donnait des commandes à exécuter pour identifier l'architecture du cluster, les modules disonible, etc. Cela n'a évidemment pas fonctionné du premier coup, après quelques jours de travail, j'ai pu créer les 3 fichiers nécessaire.