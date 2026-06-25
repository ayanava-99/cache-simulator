# cache simulator

a simple visual cache simulator built with python and streamlit
it compares least recently used and first in first out cache replacement policies
it calculates the effective memory access time to show which cache is faster on average

## features

it models a simple key value cache
you can configure the cache size
it compares lru and fifo side by side
it supports write through and write back policies
write back delays memory writes until a dirty eviction occurs

## installation

clone the repository
install requirements by running pip install r requirementstxt
run the app by running streamlit run mainpy

## traces

you can upload custom txt traces
for read use r key
for write use w key value
lines starting with hash are comments

## project files

mainpy contains the user interface and graphs
enginepy contains the simulation logic and math
parserpy reads the trace files
databasepy simulates slow memory
lrupy has the lru logic
fifopy has the fifo logic
requirementstxt lists dependencies
traces folder has demo files
