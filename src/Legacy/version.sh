#!/bin/sh -e

cd "$(dirname $(realpath $0))"

echo "debug version.sh 100"

CORPUS=$1
# overwrites it with the augmented table!
METATABLE_NAME=$2
# extracting local corpus name from the full corpus name (e.g., 'main/source' --> 'source')
NAME=$(echo $CORPUS | tr "\/" "\n" | tail -1)
# extracting root corpus name (e.g., 'main/source' --> 'main')
ROOT_CORPUS_NAME=$(echo $CORPUS | tr "\/" "\n" | head -1)
ROOT=$6
SOURCE=$ROOT/$CORPUS
COMMON=$ROOT/tables
CLEAN=$SOURCE/texts
TABLES=$SOURCE/tables
TEXTS=$7
LOGDIR=$8
SVNLOGDIR=$9
SVNLOG=$SVNLOGDIR/$NAME-svnlog.log

echo "debug version.sh 200"

mkdir -p $LOGDIR

echo "debug version.sh 300"

echo "$ROOT/$ROOT_CORPUS_NAME"
cd $ROOT/$ROOT_CORPUS_NAME
# todo commented by Anton Dyshkant for debug reasons. uncomment in production
#  svn log -v -q -r $3:$4 --xml > $SVNLOG
cd -

echo "debug version.sh 400"

if [ -e $TABLES/copyfrom-paths.txt ]
then
  COPYFROM=--copyfrom-paths=$TABLES/copyfrom-paths.txt
else
  COPYFROM=''
fi

echo "debug version.sh 500"

echo $COPYFROM

if [ $# -ge 5 ]
then
    if [ $5 = "utf" ]
    then
        echo "debug version.sh 550 utf"
      python2.7 ./version.py --utf --tablein=$TABLES/$METATABLE_NAME --tableout=$TABLES/$METATABLE_NAME.versioned --svnlog=$SVNLOG $COPYFROM
    fi
else
        echo "debug version.sh 560 NOT utf"
  python2.7 ./version.py --tablein=$TABLES/$METATABLE_NAME --tableout=$TABLES/$METATABLE_NAME.versioned --svnlog=$SVNLOG $COPYFROM
fi

echo "debug version.sh 600"

mv $TABLES/$METATABLE_NAME.versioned $TABLES/$METATABLE_NAME

echo "debug version.sh 700"

#rm $SVNLOG
