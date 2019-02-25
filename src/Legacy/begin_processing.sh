#!/usr/bin/env bash

cd "$(dirname $(realpath $0))"

if [ $# -lt 4 ]; then
    echo "Usage: begin_processing.sh <corpus name> <path to corpus root> <path to output texts> <path to logs directory>"
    exit 1
fi

set -e

corpus=$1
root=$2
texts=$3
path_to_tagging=$4
path_to_semantic_dictionary=$5
path_to_add=$6
path_to_del=$7
logs_directory=$8
svn_log_directory=$9
path_to_mystem_binary=${10}
jobs_count=${11}

./$corpus.sh $root $texts $path_to_tagging $path_to_semantic_dictionary $path_to_add $path_to_del $logs_directory $svn_log_directory $path_to_mystem_binary $jobs_count
