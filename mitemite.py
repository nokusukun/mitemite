# Mitemite
from cefpython3 import cefpython as cef
import time
import sys
import win32gui
import time


class Mite():
    j_funcs  = []
    j_obj    = []
    j_prop   = []

    def __init__(self, url, title, settings={}):
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
        self.resizeWindow(window.windowRect[0], 
                        window.windowRect[1], 
                        window.windowRect[2], 
                        window.windowRect[3])




    def resizeWindow(self, left, top, right, bottom):
        handle = self.browser.GetWindowHandle()
        win32gui.MoveWindow(handle, left, top, right, bottom, True)


    def start(self):
        self._bindJS()
        cef.MessageLoop()
        cef.Shutdown()
        pass


    def _bindJS(self):
        # Loads the javascript bindings
        bindings = cef.JavascriptBindings(
            bindToFrames=False, bindToPopups=False)
        for funcs in self.j_funcs:
            bindings.SetFunction(funcs["name"], funcs["function"])
        for obj in self.j_obj:
            bindings.SetObject(funcs["name"], funcs["function"])

        self.browser.SetJavascriptBindings(bindings)


    def jFunction(self):
        # f is the function
        def deco(f):
            self.j_funcs.append({"name": f.__name__, "function": f});
        return deco

    def onReady(self):

        def deco(f):
            self.j_funcs.append({"name": "miteUIOnReady", "function": f});
        return deco

    def jObject(self, f):
        self.j_obj.append({"name": f.__name__, "function": f});




class Materialize():
    toast = 'Materialize.toast("{0}", {1})'.format


class pquery():
    navigate = "window.location.href = '{0}';".format
    fadeIn = "$('#{0}').fadeIn({1})".format
    fadeOut = "$('#{0}').fadeOut({1})".format
    keybind = "$(document).bind('keyup', '{0}', function(){{ {1}(); }});".format
    append = "$('#{0}').append('{1}');".format


class UI():
    inputs = {}
    browser = None
    xj = None
    xf = None
    elements = {}

    def __init__(self, mite):
        self.browser = mite.browser
        self.xj_ = self.browser.ExecuteJavascript
        self.xf = self.browser.ExecuteFunction
        self.debug = True

        mite.j_funcs.append({"name": "miteUIcallback", "function": self.callback})
        mite.j_funcs.append({"name": "miteUIsetprop", "function": self.callback_new})

    def xj(self, script):
        if self.debug:
            print("[Mite UI]Execute: {0}".format(script))
        return self.xj_(script)


    def element(self, id):
        # Returns an element Object, lets you set stuff.
        return self._UIElement(self, id)

    def popup(self, header, content):
        print("UI.popup evoked: {0}, {1}".format(header, content))
        # script = "popup('{header}','{content}');".format(header=header, content=content)
        # self.browser.ExecuteJavascript(script)
        self.xf("popup", header, content)


    def get(self, id):
        # self.xf("miteUIGet", id)
        # time.sleep(0.1)
        return self.inputs[id]


    def setText(self, id, value):
        # Now defunct
        script = "$('#{id}').text('{value}');".format(id=id, value=value)
        self.xj(script)


    def setValue(self, id, value):
        # Now defunct
        script = "$('#{id}').val('{value}');".format(id=id, value=value)
        self.xj(script)


    def callback(self, id, value):
        # Now defunct
        self.inputs[id] = value

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

        def __getattr__(self, attr):
            if attr == "text":
                attr = "innerHTML"
            return self.UI.elements[self.id][attr]

        def __setattr__(self, name, value):
            try:
                script = "$('#{id}').prop('{attr}','{value}');".format(id=self.id, attr=name, value=value)
                self.UI.xj(script)
            except:
                super().__setattr__(name, value)

            # if name == "text":
            #     self.UI.setText(self.id, value)
            #         
            # if name == "value":
            #     self.UI.setValue(self.id, value)