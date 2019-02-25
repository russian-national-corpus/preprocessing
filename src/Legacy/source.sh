#!/bin/sh

cd "$(dirname $(realpath $0))"

echo "debug source.sh 100"

set -e

CORPUS=source
ROOT=$1
TEXTS=$2
path_to_tagging=$3
path_to_semantic_dictionary=$4
path_to_add=$5
path_to_del=$6
LOGS=$7
SVNLOGDIR=$8
path_to_mystem_binary=$9
jobs_count=${10}
SOURCE=$ROOT/main/$CORPUS
COMMON=$ROOT/tables
CLEAN=$SOURCE/texts
TABLES=$SOURCE/tables
PREAUG=$TEXTS/pre-augmented/$CORPUS
AUG=$TEXTS/augmented/$CORPUS
FILTERED=$TEXTS/filtered/$CORPUS
FINAL=$TEXTS/finalized/$CORPUS
USERNAME=`whoami`

echo "debug source.sh 200"

mkdir -p $LOGS
rm -rf $AUG
mkdir -p $AUG
rm -rf $FILTERED
mkdir -p $FILTERED
rm -rf $FINAL
mkdir -p $FINAL

echo "debug source.sh 300"

cd $SOURCE
#svn up
cd -

cd $COMMON
#svn up
cd -

echo "debug source.sh 400"

python2.7 validate_xml.py $CLEAN

echo "debug source.sh 500"

python2.7 ./meta.py $TABLES/$CORPUS.csv $CLEAN -check -utf

echo "debug source.sh 600"

python2.7 ./meta.py $TABLES/$CORPUS.csv $TABLES/$CORPUS.tmp -convert -utf

echo "debug source.sh 700"

./version.sh main/source $CORPUS.tmp 1 HEAD utf $ROOT $TEXTS $LOGS $SVNLOGDIR

echo "debug source.sh 800"

python2.7 $path_to_tagging/annotate_texts.py --input $CLEAN --output $AUG --semdict $path_to_semantic_dictionary --add $path_to_add --del $path_to_del --jobs $jobs_count --mystem $path_to_mystem_binary

echo "debug source.sh 900"

python2.7 validate_xml.py $AUG

echo "debug source.sh 1000"

cd filters

./do.sh $CORPUS $TEXTS

echo "debug source.sh 1100"

cd -

rm -rf $AUG

echo "debug source.sh 1200"

python2.7 ./finalize-corpus_parallel.py $TABLES/$CORPUS.tmp $FILTERED $FINAL -utf

echo "debug source.sh 1300"

rm -rf $FILTERED

echo "debug source.sh 1400"