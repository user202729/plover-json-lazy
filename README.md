# plover-json-lazy
Plover dictionary plugin to load JSON dictionaries faster the first time.

**Details**: when Plover starts, it takes about a second (depends on the dictionary size and the
processing speed) to build the lookup dictionaries (for fast lookup).

If this plugin is installed, `.json` dictionaries will delay the lookup dictionaries construction.
However, the first lookup will be delayed by about half a second.

If you want to be explicit (or if the plugin doesn't work), use `.jsonl` file extension
for the dictionaries instead.
