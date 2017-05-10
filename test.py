from mitemite import Mite, UI, Materialize, pquery
import time
import json
import glob

class app():
	mite = Mite("b:\\git-projects\\mitemite\\views\\main.html", "Mite Manga Viewer Demo")
	miteui = UI(mite)
	textbox = miteui.element("bitch")
	header = miteui.element("header")
	textbox2 = miteui.element("bitchass")
	page = miteui.element("page-view")
	viewhole = miteui.element("viewport")
	mapbox = miteui.element("map-container")

	bookdetail = {
		"title"		:"Boku no Hero Academia 11",
		"pages"		:213,
		"format"	:"jpg",
	}

	bookmeta = {}

	languageMap = {}

	session = {
		"currentpage"	:1,
		"zoom"			:80,
	}

	@mite.jFunction()
	def pythoncallback():
		miteui.popup("Hey", "hey this came from the button press Input: {0}".format(textbox.value))
		print("mite-input@bitch: " + textbox.value)
		header.innerHTML = "Old value: {0}".format(textbox.value)
		textbox.value = "This is a test value"
		textbox.style = "width: 400px;"
		textbox2.style = "width: 300px;"
		print(textbox2.outerHTML)


	@mite.jFunction()
	def dummy():
		app.miteui.xj(Materialize.toast("Function not implemented yet!", 1000))

	@mite.jFunction()
	def pageNext():
		if app.session['currentpage'] > app.bookdetail["pages"]:
			app.miteui.xj(Materialize.toast("You are on the last page.", 1000))
			return

		app.miteui.xj(pquery.fadeOut(app.page.id, 100))
		time.sleep(0.1)

		app.session['currentpage'] += 1
		app.page.src = "data/{0}.{1}".format(str(app.session['currentpage']).zfill(3), app.bookdetail["format"])
		app.header.innerHTML = "{0}@page {1}".format(app.bookdetail["title"], app.session["currentpage"])

		app.miteui.xj(pquery.navigate("#top"))
		app.miteui.xj(pquery.fadeIn(app.page.id, 100))
		app.miteui.xj("$('#view-hole').focus();")

	@mite.jFunction()
	def pagePrev():
		if app.session['currentpage'] < 2:
			app.miteui.xj(Materialize.toast("You are on the first page.", 1000))
			return

		app.miteui.xj(pquery.fadeOut(app.page.id, 100))
		time.sleep(0.1)

		app.session['currentpage'] -= 1
		app.page.src = "data/{0}.{1}".format(str(app.session['currentpage']).zfill(3), app.bookdetail["format"])
		app.header.innerHTML = "{0}@page {1}".format(app.bookdetail["title"], app.session["currentpage"])

		app.miteui.xj(pquery.navigate("#top"))
		app.miteui.xj(pquery.fadeIn(app.page.id, 100))
		app.miteui.xj("$('#view-hole').focus();")

	@mite.jFunction()
	def zoomIn():
		app.session["zoom"] += 5;
		app.viewhole.style = "width: {0}%".format(app.session["zoom"])

	@mite.jFunction()
	def zoomOut():
		app.session["zoom"] -= 5;
		app.viewhole.style = "width: {0}%".format(app.session["zoom"])

	@mite.onReady()
	def onReady():
		path = "views\\bnha\\"
		
		try:
			with open(path+"meta.txt") as f:
				app.bookmeta = json.loads(f.read())
		except:
			assert False, "Invalid Metadata"

		app.parseLangMaps(path)
		
		app.header.innerHTML = app.bookmeta["title"]
		app.page.src = "data/008.jpg"
		app.loadMap(app.languageMap["English"]["008.jpg"])

		print("Binding Keyboard Shortcuts")
		app.miteui.xj(pquery.keybind("left", "pagePrev"))
		app.miteui.xj(pquery.keybind("right", "pageNext"))

		print("App is now fully loaded")


	def loadMap(mapData):
		script = "$('#{id}').prop('innerHTML',`{value}`);".format(id="map-container", value=mapData)
		app.miteui.xj(script);
		script = "$('#page-view').prop('usemap', '#map');"
		script += "$('img[usemap]').rwdImageMaps();"
		script += "$('area').addClass('tooltipped');"
		script += "$('area').attr('data-position', 'top');"
		script += "$('.tooltipped').tooltip({delay: 10});"
		script += "$('area').attr('onmouseover', 'moveTool(event)');"
		app.miteui.xj(script);

	def parseLangMaps(path):
		for name in glob.glob(path+"*.lang.txt"):
			with open(name) as f:
				map = [x.rstrip() for x in f.readlines()]
				data = {}
				line = 0
				language = ""

				while line < len(map) - 1:
					if map[line].startswith("[lang]"):
						language = map[line].replace("[lang]", "")
						print("Language Map: {0}".format(language))
						line += 1

					if map[line].startswith("[page]"):
						page = map[line].replace("[page]", "")
						print("\tPage: {0}".format(page))
						pagemap = []
						line += 1
						try:
							while not map[line].startswith("[page]"):
								print("\t\tMap: {0}".format(map[line]))
								pagemap.append(map[line].replace("data-text", "data-tooltip"))
								line += 1
						except:
							pass

						data[page] = "".join(pagemap)

			app.languageMap[language] = data
							




app.mite.start()

