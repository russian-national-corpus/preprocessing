#!/bin/sh

cd "$(dirname $(realpath $0))"

echo "debug standard.sh 100"

set -e

CORPUS=standard
ROOT=$1
TEXTS=$2
path_to_tagging=$3
path_to_semantic_dictionary=$4
path_to_add=$5
path_to_del=$6
LOGS=$7
SVNLOGDIR=$8
path_to_mystem_binary=$9
COMMON=$ROOT/tables
SOURCE=$ROOT/main/$CORPUS
CLEAN=$SOURCE/texts
TABLES=$SOURCE/tables
AUG=$TEXTS/augmented/$CORPUS
FILTERED=$TEXTS/filtered/$CORPUS
FINAL=$TEXTS/finalized/$CORPUS
USERNAME=`whoami`

echo "debug standard.sh 200"

mkdir -p $LOGS
rm -rf $AUG
mkdir -p $AUG
rm -rf $FILTERED
mkdir -p $FILTERED
rm -rf $FINAL
mkdir -p $FINAL

echo "debug standard.sh 300"

cd $SOURCE
#svn up
cd -

cd $COMMON
#svn up
cd -

echo "debug standard.sh 400"

python2.7 validate_xml.py $CLEAN

echo "debug standard.sh 500"

python2.7 ./meta.py $TABLES/$CORPUS.csv $CLEAN -check -utf

echo "debug standard.sh 600"

python2.7 ./meta.py $TABLES/$CORPUS.csv $TABLES/$CORPUS.tmp -convert -utf

echo "debug standard.sh 700"

# ./version.sh main/standard $CORPUS.tmp 1 HEAD utf $ROOT $TEXTS $LOGS $SVNLOGDIR

echo "debug standard.sh 800"

python2.7 $path_to_tagging/semantics.py --input $CLEAN --output $AUG --semdict $path_to_semantic_dictionary --merge --mystem $path_to_mystem_binary

echo "debug standard.sh 900"

cd filters

./do.sh $CORPUS $TEXTS

echo "debug standard.sh 1000"

cd -

rm -rf $AUG

echo "debug standard.sh 1100"

python2.7 ./finalize-corpus.py $TABLES/$CORPUS.tmp $FILTERED $FINAL -utf

echo "debug standard.sh 1200"

python2.7 ./mark_everything_disamb.py $FINAL

echo "debug standard.sh 1300"

rm -rf $FILTERED

echo "debug standard.sh 1400"
