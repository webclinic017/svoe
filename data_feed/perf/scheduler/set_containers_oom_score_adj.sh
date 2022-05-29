#!/bin/bash

# Script setting oom_score_adj for running containers
# Example: ./set_containers_oom_score_adj -n minikube-1-m02 -c "pod1_redis pod1_data-feed-container" -s "-1000"
# -n node name
# -c should be in quotes e.g. -c "container1 container2 container3"
# -s score
while getopts ":n:c:s:" opt; do
  case $opt in
    n) node="$OPTARG"
    ;;
    c) containers="$OPTARG"
    ;;
    s) oom_score_adj="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac

done
# calculate number of containers
arr_c=($containers)
len=${#arr_c[@]}

# name_regex="part1|part2|part3"
names_regex=""
for cname in $containers
do
  names_regex+="$cname|"
done
names_regex=${names_regex%?} # remove last |
shell_command=(
  "
  set -e
  ids=\$(docker ps -f name=\"$names_regex\" | awk '{print \$1}' | tail -n +2 )
  arr_ids=(\$ids)
  pids=\$(docker inspect -f '{{.State.Pid}}' \$ids)
  arr_pids=(\$pids)
  len=\${#arr_pids[@]}

  if [[ \"\$len\" -ne $len ]]; then
    echo \"Error: Number of requested containers differs from number of processes. Check container names\"
    exit 1
  fi

  for pid in \$pids
  do
    echo \"$oom_score_adj\" > proc/\$pid/oom_score_adj
  done

  echo \"Success\"
  "
)

kubectl node-shell $node -- bash -c "${shell_command[@]}"
