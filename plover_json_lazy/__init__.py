import codecs

try:
    import simplejson as json
except ImportError:
    import json
import threading

from plover.steno_dictionary import StenoDictionary as DefaultStenoDictionary
from plover.steno import normalize_steno


class StenoDictionary(DefaultStenoDictionary):
    def __init__(self)->None:
        super().__init__()
        self._auxiliary_structures_initialized = False
        # auxiliary: reverse, casereverse
        # they are only necessary for (word to stroke, reverse) lookup, not normal dict usage

        #self._auxiliary_structures_lock = threading.Lock()
        # this is not necessary if there's only ever one thread access the dictionary

        #NOTE currently threads are not used. Ensure that multithreading logic is correct is really hard.

    def _ensure_auxiliary_initialized(self)->None:
        if 1:#with self._auxiliary_structures_lock:
            if self._auxiliary_structures_initialized: return

            reverse = self.reverse
            casereverse = self.casereverse
            assert not (reverse or casereverse)

            for key, value in self._dict.items():
                reverse[value].append(key)
                casereverse[value.lower()].append(value)

            self._auxiliary_structures_initialized=True

    def update(self, *args, **kwargs)->None:
        assert not self.readonly
        iterable_list = [
            a.items() if isinstance(a, (dict, StenoDictionary))
            else a for a in args
        ]
        if kwargs:
            iterable_list.append(kwargs.items())
        if not self._dict:
            if 1:#with self._auxiliary_structures_lock:
                self._auxiliary_structures_initialized=False
                self._dict = dict(*iterable_list)
                longest_key = self._longest_key
                assert not longest_key
                # NOTE
                for key, value in self._dict.items():
                    key_len = len(key)
                    if key_len > longest_key:
                        longest_key = key_len
                self._longest_key = longest_key
        else:
            for iterable in iterable_list:
                for key, value in iterable:
                    self[key] = value

    #def clear(self)->None:
    #    if 1:#with self._auxiliary_structures_lock:
    #        super().clear()

    def __setitem__(self, key, value)->None:
        assert not self.readonly
        if key in self:
            del self[key]
        self._longest_key = max(self._longest_key, len(key))
        self._dict[key] = value
        if self._auxiliary_structures_initialized:
            self.reverse[value].append(key)
            self.casereverse[value.lower()].append(value)

    def __delitem__(self, key)->None:
        assert not self.readonly
        value = self._dict.pop(key)
        if self._auxiliary_structures_initialized:
            self.reverse[value].remove(key)
            self.casereverse[value.lower()].remove(value)
        if len(key) == self.longest_key:
            if self._dict:
                self._longest_key = max(len(x) for x in self._dict)
            else:
                self._longest_key = 0

    def reverse_lookup(self, value)->None: # value -> key
        self._ensure_auxiliary_initialized()
        return super().reverse_lookup(value)

    def casereverse_lookup(self, value)->None: # value.lower() -> value (NOT key!)
        self._ensure_auxiliary_initialized()
        return super().casereverse_lookup(value)


class LazyJsonDictionary(StenoDictionary):

    def _load(self, filename)->None:
        with open(filename, 'rb') as fp:
            contents = fp.read()
        for encoding in ('utf-8', 'latin-1'):
            try:
                contents = contents.decode(encoding)
            except UnicodeDecodeError:
                continue
            else:
                break
        else:
            raise ValueError('\'%s\' encoding could not be determined' % (filename,))
        d = json.loads(contents)
        self.update((normalize_steno(x[0]), x[1]) for x in d.items())

    def _save(self, filename)->None:
        with open(filename, 'wb') as fp:
            writer = codecs.getwriter('utf-8')(fp)
            json.dump({'/'.join(k): v for k, v in self.items()},
                      writer, ensure_ascii=False, sort_keys=True,
                      indent=0, separators=(',', ': '))
            writer.write('\n')
