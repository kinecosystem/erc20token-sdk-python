#!/usr/bin/env bash

# Executes cleanup function at script exit.
#trap cleanup EXIT

# Test if testrpc is running on port $1.
# Result is in $?
testrpc_running() {
  nc -z localhost $1
}

# Kills testrpc process with its PID in $testrpc_pid.
cleanup() {
  echo "cleaning up"
  # Kill the testrpc instance that we started (if we started one).
  if [ -n "$testrpc_pid" ]; then
    kill -9 $testrpc_pid
  fi
}

balance=100000000000000000000

if testrpc_running 8545; then
  echo "Using existing testrpc instance"
else
  echo "Starting testrpc instance on port 8545"
  testrpc --account=0x11c98b8fa69354b26b5db98148a5bc4ef2ebae8187f651b82409f6cefc9bb0b8,"$balance" \
        --account=0xc5db67b3865454f6d129ec83204e845a2822d9fe5338ff46fe4c126859e1357e,"$balance" \
        -u 0 -u 1 -p 8545 --gasLimit 0xfffffffffff > testrpc.log 2>&1 & testrpc_pid=$!
fi


