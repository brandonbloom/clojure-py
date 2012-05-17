#!/usr/bin/env python

import sys
import imp
import os.path
import traceback

from clojure.lang.symbol import symbol
from clojure.lang.var import Var, intern as internVar
from clojure.util.byteplay import *

# Create a PEP 302 import hook
class MetaImporter(object):
    def find_module(self, fullname, path=None):
        lastname = fullname.rsplit('.', 1)[-1]
        for d in path or sys.path:
            clj = os.path.join(d, lastname + ".clj")
            pkg = os.path.join(d, lastname, "__init__.py")
            pkgc = getattr(imp, "cache_from_source",
                           lambda path: path + "c")(pkg)
            if (os.path.exists(clj) and
                not (os.path.exists(pkg) or os.path.exists(pkgc))):
                self.path = clj
                return self
        return None

    def load_module(self, name):
        if name not in sys.modules:
            sys.modules[name] = None # avoids circular imports
            try:
                requireClj(self.path)
            except:
                del sys.modules[name]
                raise ImportError
            sys.modules[name].__loader__ = self
        if sys.modules[name] == None:
            del sys.modules[name]
            raise ImportError
        return sys.modules[name]

from clojure.lang.lispreader import read
from clojure.lang.fileseq import StringReader
from clojure.lang.globals import currentCompiler
import clojure.lang.rt as RT
from clojure.lang.compiler import Compiler
from clojure.lang.symbol import Symbol, symbol
from clojure.lang.var import pushThreadBindings, popThreadBindings
import cPickle

VERSION = "0.2.4"


sys.meta_path.append(MetaImporter())


def requireClj(filename, stopafter=None):
    with open(filename) as fl:
        r = StringReader(fl.read())

    RT.init()
    comp = Compiler()
    comp.setFile(filename)
    
    pushThreadBindings({currentCompiler: comp})

    #o = open(filename+".cljc", "w")
    try:
        while True:
            EOF = object()
            s = read(r, False, EOF, True)
            if s is EOF:
                break
            #cPickle.dump(s, o)
            try:
                res = comp.compile(s)
                comp.executeCode(res)
                if stopafter is not None and hasattr(comp.getNS(), stopafter):
                    break
            except Exception as exp:
                print s, filename
                raise
    except IOError as e:
        pass
    finally:
        popThreadBindings()

    #o.close()

#requireClj(os.path.dirname(__file__) + "/core.clj")
import clojure.core

def main():
    RT.init()
    comp = Compiler()
    
    pushThreadBindings({currentCompiler: comp})
    
    try:
    
        if not sys.argv[1:]:
            import clojure.repl
            clojure.repl.enable_readline()
            clojure.repl.run_repl(comp)
        else:
            for x in sys.argv[1:]:
                if x.endswith('.clj'):
                    requireClj(x)
    finally:
        popThreadBindings()

if __name__ == "__main__":
    main()
