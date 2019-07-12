#!/usr/bin/env python3
#
# Lua miniirc wrapper
#
# © 2019 by luk3yx.
#

import miniirc, os, sys, threading
from miniirc_extras import AbstractIRC, utils
from typing import Any, Callable, Optional, Union
import lupa # type: ignore

@lupa.unpacks_lua_table
def _unpack_lua_table(*args, **kwargs):
    return args, kwargs

# Wrap functions so they work nicely
class _FunctionWrapper:
    def _lua_args(self, args: tuple):
        for arg in args:
            if isinstance(arg, (tuple, list, dict)):
                yield self._lua.table_from(arg)
            else:
                yield arg

    # Make await() work
    def __call__(self, *args):
        co = self._func.coroutine(*self._lua_args(args))
        try:
            res = co.send(None)

            while res and isinstance(res, tuple) and callable(res[0]):
                if not res[0]:
                    print(res[-1], file=sys.stderr)
                    return

                args, kwargs = _unpack_lua_table(*res[1:])
                try:
                    data = res[0](*args, **kwargs)
                except Exception as e:
                    res = co.send((False, type(e).__name__ + ': ' + str(e)))
                else:
                    res = co.send((True, data))
                    del data
        except lupa.LuaError as e:
            print(e, file=sys.stderr)
            try:
                print(self._tb(co), file=sys.stderr)
            except:
                pass
        except (RuntimeError, StopIteration):
            pass

    def __init__(self, lua: lupa.LuaRuntime, func):
        if not callable(func):
            raise TypeError('_FunctionWrapper expects a callable object.')
        self._lua = lua
        self._func = func
        self._tb = self._lua.globals().debug.traceback
        assert hasattr(func, 'coroutine') and callable(func.coroutine)

# Wrap Handler functions
class _HandlerFuncWrapper:
    __slots__ = ('_lua', '_func')

    @lupa.unpacks_lua_table_method
    def __call__(self, *events, colon: bool = False,
            func: Optional[Callable] = None, **kwargs) -> Optional[Callable]:
        add_handler = self._func(*events, colon=colon, **kwargs)
        if func is None:
            return lambda func : add_handler(_FunctionWrapper(self._lua, func))
        else:
            add_handler(_FunctionWrapper(self._lua, func))
            return func

    def __eq__(self, other):
        return self._func == other

    def __ne__(self, other):
        return self._func != other

    def __init__(self, lua: lupa.LuaRuntime, func: Callable) -> None:
        self._lua = lua
        self._func = func

# Wrap lua runtimes
class RuntimeWrapper:
    __slots__ = ('dofile', 'loadstring', 'lua', '_handlers', '_await')

    # Some inital code
    _code = rb"""
    if table.unpack then
        unpack = table.unpack
    else
        table.unpack = assert(unpack)
    end

    if loadstring then
        load = loadstring
    else
        loadstring = load
    end

    function import(...)
        local n = select('#', ...)
        local res = {}
        for i = 1, n do
            local name = select(i, ...)
            if name == 'miniirc' and miniirc then
                table.insert(res, miniirc)
            else
                table.insert(res, python.builtins.__import__(name))
            end
        end
        return table.unpack(res)
    end

    local _miniirc, lupa, time = import('miniirc', 'lupa', 'time')

    miniirc = {
        Handler = _miniirc.Handler,
        CmdHandler = _miniirc.CmdHandler,
        IRC = lupa.unpacks_lua_table(_miniirc.IRC),
        ver = {},
    }

    do
        for i in python.iter(_miniirc.ver) do table.insert(miniirc.ver, i) end
    end

    -- Create await()
    function await(func, ...)
        local good, msg
        local n = select('#', ...)
        if n == 0 and type(func) == 'table' then
            good, msg = coroutine.yield(table.remove(func, 1), func)
        elseif n < 2 then
            good, msg = coroutine.yield(func, {...})
        end
        if not good then error(msg, 2) end
        return msg
    end

    -- A nicer time.sleep() wrapper
    function sleep(seconds)
        if type(seconds) ~= 'number' then
            error('sleep() expects a number, not ' .. type(seconds) .. '.', 2)
        elseif seconds < 0 then
            error('sleep() length must be non-negative.', 2)
        elseif seconds == 0 then
            return
        end

        local thread, main = coroutine.running()
        if not thread or main then
            time.sleep(seconds)
        else
            await(time.sleep, seconds)
        end
    end
    """.replace(b'\n    ', b'\n')

    # Override Handlers
    def _getter(self, obj, attr_name):
        if attr_name in ('Handler', 'CmdHandler') and (obj is miniirc
                or isinstance(obj, (AbstractIRC, utils.HandlerGroup))):
            return _HandlerFuncWrapper(self.lua, getattr(obj, attr_name))

        res = getattr(obj, attr_name)
        return res

    @property
    def globals(self):
        return self.lua.globals

    # Create a new class right away
    @classmethod
    def run(cls, file: str) -> None:
        cls().dofile(file)

    @property
    def eval(self) -> Callable[[Union[str, bytes]], Any]:
        return self.lua.eval

    @property
    def exec(self) -> Callable[[Union[str, bytes]], Any]:
        return self.lua.execute

    def wrap_lua_function(self, func: Callable) -> Callable:
        """ Wraps a lua function so await() will work. """
        if not callable(getattr(func, 'coroutine', None)):
            raise TypeError('wrap_lua_function() expects a Lua function.')
        return _FunctionWrapper(self.lua, func)

    def call_async(self, func: Callable, *args, **kwargs):
        return self.wrap_lua_function(func)(*args, **kwargs)

    def __init__(self, clone: bool = False) -> None:
        self.lua = lupa.LuaRuntime(attribute_handlers=(self._getter, setattr))
        globs = self.lua.globals()
        assert __file__.endswith('.py')
        self.dofile = globs.dofile # type: Callable[[str], Any]
        self.exec(self._code)
        self.loadstring = globs.loadstring # type: Callable[[Union[str, bytes]], Callable]

run = RuntimeWrapper.run

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='The lua file to run.')
    args = parser.parse_args()
    wrapper = RuntimeWrapper()

    try:
        res = wrapper.dofile(args.file)

        if callable(res):
            wrapper.call_async(res)
    except lupa.LuaError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
