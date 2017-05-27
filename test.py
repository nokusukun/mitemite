from mitemite import Mite, UI, Materialize, pquery
from mitemite import Query as q
from mitemite import ElementBuilder
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

	# This just exposes the fucntion to the javascript engine
	@mite.jFunction()
	def pythoncallback(self):
		miteui.popup("Hey", "hey this came from the button press Input: {0}".format(textbox.value))
		print("mite-input@bitch: " + textbox.value)
		header.innerHTML = "Old value: {0}".format(textbox.value)
		textbox.value = "This is a test value"
		textbox.style = "width: 400px;"
		textbox2.style = "width: 300px;"
		print(textbox2.outerHTML)


	# Binds this function to these buttons on the 'onmouseover' event
	@mite.jFunction(["btn-nav-libr", "btn-nav-open", "btn-nav-sett"], "onmouseover")
	def dummy(self):
		app.mite.xj(Materialize.toast("Function not implemented yet!", 1000))

	# Binds this function to this button on the 'onclick' event by default
	@mite.jFunction("btn-next")
	def pageNext(self):
		if app.session['currentpage'] > app.bookdetail["pages"]:
			app.mite.xj(Materialize.toast("You are on the last page.", 1000))
			return

		# app.mite.xj(pquery.fadeOut(app.page.id, 100))
		# time.sleep(0.1)

		app.session['currentpage'] += 1
		app.page.src = "data/{0}.{1}".format(str(app.session['currentpage']).zfill(3), app.bookdetail["format"])
		app.header.innerHTML = "{0}".format(app.bookdetail["title"])

		# Old functions pre miteJquery
		# app.mite.xj(pquery.fadeIn(app.page.id, 100))
		# app.mite.xj("$('#view-hole').focus();")


		chip = ElementBuilder("span").c("chip").text('Page {0}'.format(app.session['currentpage']))
		app.renderPageSlider(0, app.bookdetail["pages"])
		# chip = q(Materialize.chip).text('Page {0}'.format(app.session['currentpage']))
		query = q(app.miteui.element("page-pos-container")).append(chip) + \
				q(app.page).fadeIn(100) + \
				q(app.miteui.element("page-pos")).val(app.session['currentpage']) + \
				q("#view-hole").animate("{scrollTop: 0}", 200).focus()
		query.execute(app.mite)




	@mite.jFunction("btn-prev")
	def pagePrev(self):
		if app.session['currentpage'] < 2:
			app.mite.xj(Materialize.toast("You are on the first page.", 1000))
			return

		app.mite.xj(pquery.fadeOut(app.page.id, 100))
		time.sleep(0.1)

		app.session['currentpage'] -= 1
		app.page.src = "data/{0}.{1}".format(str(app.session['currentpage']).zfill(3), app.bookdetail["format"])
		app.header.innerHTML = "{0}".format(app.bookdetail["title"])
		q(app.header).append(
			q(Materialize.chip).addClass('new').text('Page {0}'.format(app.session['currentpage']))).execute(app.mite)

		q(app.page).fadeIn(100).execute(app.mite)
		q(app.miteui.element("view-hole")).focus().execute(app.mite)


	@mite.jFunction("btn-zoom-in")
	def zoomIn(self):
		app.session["zoom"] += 5;
		app.viewhole.style = "width: {0}%".format(app.session["zoom"])

	@mite.jFunction("btn-zoom-out")
	def zoomOut(self):
		app.session["zoom"] -= 5;
		app.viewhole.style = "width: {0}%".format(app.session["zoom"])

	@mite.jFunction()
	def jumpToPage(self, value):
		app.session['currentpage'] = int(value) - 1

	@mite.jFunction()
	def nextBottom(self, value):
		print(value)
		pass

	@mite.onReady()
	def onReady(self):
		print("Binding Keyboard Shortcuts")
		app.mite.xj(pquery.keybind("left", "pagePrev"))
		app.mite.xj(pquery.keybind("right", "pageNext"))
		print("App is now fully loaded")
		q(app.header).text("App is ready").execute(app.mite)
		app.renderPageSlider("0", app.bookdetail["pages"])
		# q("#view-hole").attr("onscroll","nextBottom({})".format(q("this").scrollTop())).execute(app.mite)

		
	def renderPageSlider(min, max):
		inp = ElementBuilder("input").id("page-pos").type("range").min(min).max(max).value(0).onchange("jumpToPage(this.value);pageNext()")
			
		app.miteui.element("page-pos-container").innerHTML = inp.html




	# DEMO STUFF
	def loadDemo():
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



	def loadMap(mapData):
		script = "$('#map-container').prop('innerHTML',`{value}`);".format(value=mapData)
		app.mite.xj(script);

		script = "$('#page-view').prop('usemap', '#map');"
		script += "$('img[usemap]').rwdImageMaps();"
		script += "$('area').addClass('tooltipped');"
		script += "$('area').attr('data-position', 'top');"
		script += "$('.tooltipped').tooltip({delay: 10});"
		script += "$('area').attr('onmouseover', 'moveTool(event)');"
		app.mite.xj(script);

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
							


app.mite.jObject(app)
app.mite.start()

