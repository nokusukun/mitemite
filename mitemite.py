# Mitemite
from cefpython3 import cefpython as cef
from decorator import decorator
import time
import sys
import win32gui
import time
import inspect
import threading
import enum
import random

# Patched Javascript Bindings to allow uninitalized classes to be used as a function
class PatchedBinder(cef.JavascriptBindings):

    def SetProperty(self, name, value):
        allowed = self.IsValueAllowedRecursively(value) # returns True or string.
        if allowed is not True:
            raise Exception("JavascriptBindings.SetProperty() failed: name=%s, "
                            "not allowed type: %s (this may be a type of a nested value)"
                            % (name, allowed))

        valueType = type(value)
        if PatchedBinder.IsFunctionOrMethod(valueType):
            self.functions[name] = value
        else:
            self.properties[name] = value

    @staticmethod
    def IsFunctionOrMethod(valueType):
        
        if ('function' in str(valueType) or 'method' in str(valueType) or'type' in str(valueType) or 'Event' in str(valueType)):
            return True
        return False

    @staticmethod
    def IsValueAllowedRecursively(value, recursion=False):
        # When making changes here modify also Frame.SetProperty() as it
        # checks for FunctionType, MethodType.
        valueType = type(value)
        valueType2 = None
        key = None

        if valueType == list:
            for val in value:
                valueType2 = JavascriptBindings.IsValueAllowedRecursively(val, True)
                if valueType2 is not True:
                    return valueType2.__name__
            return True
        elif valueType == bool:
            return True
        elif valueType == float:
            return True
        elif valueType == int:
            return True
        elif 'Event' in str(valueType):
            return True
        elif valueType == type(None):
            return True
        elif PatchedBinder.IsFunctionOrMethod(valueType):
            if recursion:
                return valueType.__name__
            else:
                return True
        elif valueType == dict:
            for key in value:
                valueType2 = JavascriptBindings.IsValueAllowedRecursively(value[key], True)
                if valueType2 is not True:
                    return valueType2.__name__
            return True
        elif valueType == str or valueType == bytes:
            return True
        elif valueType == tuple:
            return True
        else:
            return valueType.__name__


# This is an event object, please don't touch this.
# This gets called by the cef browser.
class Event():
    mite = None
    function = None
    async = True
    def __init__(self, *fargs):
        self.mite.pbug("Event {} called. Args: {}".format(self.function.__name__, fargs))
        if self.async:
            threading.Thread(target=self.function, args=fargs).start()
        else:
            self.function(*fargs)


class Mite():
    j_funcs  = []
    j_obj    = []
    j_prop   = []
    debug = True
    synchronized = []

    def __init__(self, url, title, settings={}):
        # self.pbug("Patching CEFPYTHON")
        # cef.JavascriptBindings.IsValueAllowedRecursively = Mite.IsValueAllowedRecursively
        self.pbug("Initalizing mitemite")
        sys.excepthook = cef.ExceptHook
        cef.Initialize(settings=settings)

        window = cef.WindowInfo()
        if "window" in settings:
            window.windowRect = settings["window"]
        else:
            window.windowRect = [50, 50, 800, 600]


        self.browser = cef.CreateBrowserSync(url=url,
                                    window_title=title,
                                    window_info=window)

        handle = self.browser.GetWindowHandle()
        self.pbug("Resizing UI")
        self.resizeWindow(window.windowRect[0], 
                        window.windowRect[1], 
                        window.windowRect[2], 
                        window.windowRect[3])


    def pbug(self, args):
        class bcolors:
            HEADER =    '\033[95m'
            OKBLUE =    '\033[94m'
            OKGREEN =   '\033[92m'
            WARNING =   '\033[93m'
            FAIL =      '\033[91m'
            ENDC =      '\033[0m'
            BOLD =      '\033[1m'
            UNDERLINE = '\033[4m'
        if self.debug:
            print("{0}[{a}.{b}]{1}{c}{2}".format(bcolors.HEADER, bcolors.OKBLUE, bcolors.ENDC,
                a=inspect.stack()[2][3],b=inspect.stack()[1][3], c=args))

    def javascriptErrorCallback(self, error, url, line, five, six):
        class bcolors:
            HEADER = '\033[95m'
            OKBLUE = '\033[94m'
            OKGREEN = '\033[92m'
            WARNING = '\033[93m'
            FAIL = '\033[91m'
            ENDC = '\033[0m'
            BOLD = '\033[1m'
            UNDERLINE = '\033[4m'
        print("{0}[mite.js.{a}]{1}{c} | {five} | {six}{2}".format(bcolors.FAIL, bcolors.WARNING, bcolors.ENDC,
                                                a=line, c=error, five=five, six=six))


    def xj(self, script):
        """
            xj =  Executes a javascript file
            script = The javascript in string format.
        """
        self.pbug("Executing > {0}".format(script))
        script = "try {{ {0} }} catch(e) {{ miteErrorCallback(String(e), e, 'execute', '', '');}}".format(script)
        return self.browser.ExecuteJavascript(script)



    def resizeWindow(self, left, top, right, bottom):
        handle = self.browser.GetWindowHandle()
        win32gui.MoveWindow(handle, left, top, right, bottom, True)


    def start(self):
        self.pbug("Starting Application".format())
        self.j_funcs.append({"name": "miteErrorCallback", "function": self.javascriptErrorCallback, "async": False})
        self.j_funcs.append({"name": "preReadyInit", "function": self.preReadyInitalizatize, "async": False})
        self.pbug("Appending Javascript Functions...".format())
        self._bindJS()
        cef.MessageLoop()
        cef.Shutdown()
        pass


    def preReadyInitalizatize(self):
        """
            preReadyInitalizatize = Gets Executed before the app gets ready and 
                executes any onReady functions.
        """
        self.pbug("Pre Ready Initalization")
        self.xj("window.onerror = miteErrorCallback")
        for funcs in self.j_funcs:
            if "bind" in funcs:
                    for bind in funcs["bind"]:
                        self.pbug("Binding {0} function to #{1}".format(bind, funcs["name"]))
                        script = "$('#{0}').attr('{1}', '{2}()');".format(bind, funcs["event"], funcs["name"])
                        self.xj(script)
        self.pbug("Mite Load Finished")



    def _bindJS(self):
        """
            _bindJS    = Internal function to bind the app functions to
                            the HTML elements.
        """
        # Loads the javascript bindings
        bindings = PatchedBinder(
            bindToFrames=False, bindToPopups=False)

        for funcs in self.j_funcs:

            # Create an new Event Instance for thread creation
            event = type("Event_{}".format(funcs["name"]), (Event,), {})
            event.function = funcs["function"]
            event.mite = self
            event.async = funcs["async"]

            self.pbug("Binding {0} to {1}".format(funcs["name"], funcs["function"]))
            bindings.SetFunction(funcs["name"], event)

        for obj in self.j_obj:
            self.pbug("Loading {1} as {0}".format(obj["name"], obj["function"]))
            bindings.SetObject(obj["name"], obj["function"])

        self.browser.SetJavascriptBindings(bindings)


    # DECORATOR #
    def jFunction(self, bind=None, event="onclick"):
        """
            jFucntion   = decorator to expose functions to the GUI
            --params--
                bind    = ID of the HTML Element
                event   = type of event the function will trigger.
                            Defaults to onclick

            Leaving the parameters empty just exposes it in 
                the javascript engine.
        """
        # f is the function
        def deco(f):
            # Im so sorry
            nonlocal bind, event
            function = {"name": f.__name__, "function": f}
            
            if bind is not None:
                self.pbug("Bind to: {0}".format(bind))
                if not isinstance(bind, list):
                    bind = [bind]

                new_bind = []
                for b in bind:
                    if b.startswith("#"):
                        new_bind.append(b[1:])
                    else:
                        new_bind.append(b)


                function["bind"] = new_bind
                function["event"] = event

            function["async"] = True
            self.pbug("FunctionBind: {}".format(function))
            # self.events[function["name"]] = f
            self.j_funcs.append(function)

        return deco


    def jFunctionSync(self, bind=None, event="onclick"):
        """
            jFucntion   = decorator to expose functions to the GUI
            --params--
                bind    = ID of the HTML Element
                event   = type of event the function will trigger.
                            Defaults to onclick

            Leaving the parameters empty just exposes it in 
                the javascript engine.
        """
        # f is the function
        def deco(f):
            # Im so sorry
            nonlocal bind, event
            function = {"name": f.__name__, "function": f}
            
            if bind is not None:
                self.pbug("Bind to: {0}".format(bind))
                if not isinstance(bind, list):
                    bind = [bind]

                new_bind = []
                for b in bind:
                    if b.startswith("#"):
                        new_bind.append(b[1:])
                    else:
                        new_bind.append(b)


                function["bind"] = new_bind
                function["event"] = event

            function["async"] = False
            self.pbug("FunctionSyncBind: {}".format(function))
            # self.events[function["name"]] = f
            self.j_funcs.append(function)

        return deco


    # DECORATOR #
    def onReady(self):

        def deco(f):
            self.j_funcs.append({"name": "miteUIOnReady", "function": f, "async": True});
        return deco

    # DECORATOR #
    def jObject(self, f):
        self.j_obj.append({"name": f.__name__, "function": f});






class Materialize():
    toast = 'Materialize.toast("{0}", {1})'.format
    card = '<div class="card"></div>'
    badge = '<span class="badge"></span>'
    chip = '<div class="chip"></div>' 

class pquery():
    navigate = "window.location.href = '{0}';".format
    fadeIn = "$('#{0}').fadeIn({1})".format
    fadeOut = "$('#{0}').fadeOut({1})".format
    keybind = "$(document).bind('keyup', '{0}', function(){{ {1}(); }});".format
    append = "$('#{0}').append('{1}');".format


class Map(dict):
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Map, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Map, self).__delitem__(key)
        del self.__dict__[key]


class ElementBuilder():

    def __init__(self, element):
        self.element = element
        self._property = ""
        self.properties = Map({})
        self.innerHTML = ""

    def magic_smoke(self, arg, append = False):
        if self._property == "text":
            if append:
                self.innerHTML += str(arg)
            else:
                self.innerHTML = str(arg)
        else:
            if append:
                if self._property in self.properties:
                    self.properties[self._property] += " " + arg
                else:
                    self.properties[self._property] = arg
            else:
                self.properties[self._property] = arg

        return self

    def __str__(self):
        return self.html


    def __getattr__(self, property):

        if property == "html":
            props = " ".join(["{0}='{1}'".format(x, self.properties[x]) for x in self.properties.keys()])
            build = "<{0} {1}>{2}</{0}>".format(self.element, props, self.innerHTML)
            return build

        self._property = property

        if property == "_class" or property == "c":
            self._property = "class"

        return self.magic_smoke
            



class Query():

    def __init__(self, identifier):
        self.function = ""
        self._name = ""

        if identifier == "this":
            self._query = "$({0})".format(identifier)
        elif str(identifier).startswith("$"):
            self._query = "$({0})".format(identifier)
        else:
            self._query = "$('{0}')".format(identifier)

    def magic_smoke(self, *args):
        if len(args) > 0:
            nwarg = []
            for a in args:
                if type(a) is str:
                    try:
                        if a[0] == "{" and a[-1:] == "}":
                            nwarg.append('{0}'.format(a))
                        else:
                            nwarg.append('`{0}`'.format(a))
                    except:
                        nwarg.append('`{0}`'.format(a))
                elif type(a) is Element:
                    nwarg.append('`{0}`'.format(str(a)))
                else:
                    nwarg.append(str(a))

            # could use just ", ".join(nwarg) itself, but I think it has
            # something to do with the older verion where it's "`{0}`"
            arg = "{0}".format(", ".join(nwarg))
        else:
            arg = ""

        self._query += ".{0}({1})".format(self._name ,arg)
        return self

    

    def execute(self, mite):
        mite.xj(self._query+";")

    def __str__(self):
        return self._query

    def __add__(self, other):
        self._query = self._query + ";" + other._query
        return self

    def __getattr__(self, name):
        if name == "q":
            return self._query

        self._name = name
        return self.magic_smoke





class UI():
    inputs = {}
    browser = None
    xj = None
    xf = None
    elements = {}
    get_object = {}

    def __init__(self, mite):
        self.mite = mite
        self.browser = mite.browser
        self.xj_ = self.browser.ExecuteJavascript
        self.xf = self.browser.ExecuteFunction
        self.debug = True

        mite.j_funcs.append({"name": "miteUIsetprop", "function": self.callback_new, "async": False})
        mite.j_funcs.append({"name": "getcallback", "function": self.getcallback, "async": True})

    def xj(self, script):
        self.mite.pbug("Execute > {0}".format(script))
        return self.xj_(script)


    def element(self, id):
        # Returns an element Object, lets you set stuff.
        return self._UIElement(self, id)


    def getcallback(self, id, var):
        self.get_object[id] = var


    def callback_new(self, id_, value):
        # Callback for the javascript engine.
        # Gets called everytime an element gets modified
        if not id_ in self.elements:
            self.elements[id_] = {}

        # print("SET: {0}".format(id_))
        for prop in value:
            self.elements[id_][prop[0]] = prop[1]


    class _UIElement():
        def __init__(self, UI, id):
            self.id = id
            self.UI = UI
            UI.elements[id] = {}

        def prop(self, prop):
            id_ = "".join([ str(random.randint(0, 9)) for x in range(0, 16) ])
            script = "getcallback('{id_}',$('#{id}').prop(`{prop}`));".format(id=self.id, prop=prop, id_=id_)
            self.UI.xj(script)

            while not id_ in self.UI.get_object:
                pass

            return self.UI.get_object[id_]

        def attr(self, attr, value=None):
            id_ = "".join([ str(random.randint(0, 9)) for x in range(0, 16) ])
            if value is None:
                script = "getcallback('{id_}',$('#{id}').attr(`{prop}`));".format(id=self.id, prop=attr, id_=id_)
            else:
                script = "getcallback('{id_}',$('#{id}').attr(`{prop}`, `{value}`));".format(id=self.id, id_=id_, prop=attr, value=value)

            self.UI.xj(script)

            while not id_ in self.UI.get_object:
                pass

            return self.UI.get_object[id_]


        def __getattr__(self, attr):
            if attr == "text":
                attr = "innerHTML"
            self.prop(attr)
            #return self.UI.elements[self.id][attr]

        def __str__(self):
            return "#"+self.id

        def __setattr__(self, name, value):
            try:
                script = "$('#{id}').prop(`{attr}`,`{value}`);".format(id=self.id, attr=name, value=value)
                self.UI.xj(script)
            except:
                super().__setattr__(name, value)

            # if name == "text":
            #     self.UI.setText(self.id, value)
            #         
            # if name == "value":
            #     self.UI.setValue(self.id, value)
