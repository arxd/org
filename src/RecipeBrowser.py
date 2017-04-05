
import tkinter as tk
import sys
from PlainTxtDB import DB
from Food import *

class LabelEdit(object):
	def __init__(self, parent, name, row=0, col=0, colspan=1):
		self.name = name
		self.food = None
		tk.Label(parent, text=name+':').grid(row=row, column=col, sticky=tk.E)
		self.val = tk.StringVar()
		
		self.entry = tk.Entry(parent)
		self.entry['textvariable'] = self.val
		self.entry['validate'] = 'focusout'
		self.entry['validatecommand'] = (parent.register(getattr(self, 'on_change')), '%s')
		self.entry.grid(row=row, column=col+1, columnspan=colspan, sticky=tk.W+tk.E)
		
	def set(self, food):
		self.food = food
		self.entry['validate'] = 'none'
		if self.food:
			self.update()
		else:
			self.val.set("")
		self.entry['validate'] = 'focusout'
	
	def update(self):
		self.entry['fg'] = 'black'
		self.val.set(str(getattr(self.food, self.name)))
		
	def on_change(self, value):
		setattr(self.food, self.name, value)
		return True
		
class TagsEdit(LabelEdit):
	def update(self):
		self.val.set(",".join(getattr(self.food, self.name)))
		
	def on_change(self, value):
		tags = [x.strip() for x in value.split(',') if x.strip()]
		setattr(self.food, self.name, tags)
		return True
		
		
class FloatEdit(LabelEdit):
	def update(self):
		val = getattr(self.food, self.name)
		self.val.set("" if val == -1.0 else str(val))

	def on_change(self, value):
		try:
			if not value.strip():
				value = -1.0
			f = float(value)
			setattr(self.food, self.name, f)
			self.entry['fg'] = 'black'
			return True
		except:
			self.entry['fg'] = 'red'
			return False


class FoodView(tk.LabelFrame):
	def __init__(self, parent, foodlist, **kwargs):
		tk.LabelFrame.__init__(self, parent, text="Food", **kwargs)
		self.foodlist = foodlist
		self.rowconfigure(5, weight=1)
		self.columnconfigure(1, weight=1)
		self.columnconfigure(3, weight=1)
		
		self.entries = [
			LabelEdit(self, "description", row=0, colspan=3),
			TagsEdit(self, "tags", row=1, colspan=3),
			FloatEdit(self, "unit_mass",row=2),
			FloatEdit(self, "unit_volume", row=3),
			LabelEdit(self, "unit_label", row=4),
			FloatEdit(self, "kcals", row=2, col=2),
			FloatEdit(self, "protein", row=3, col=2),
			FloatEdit(self, "carbs", row=4, col=2)
		]
		
		bottom = tk.PanedWindow(self, orient=tk.VERTICAL)
		bottom.grid(row=5, column=0, columnspan=4, sticky=tk.NW+tk.SE)
		ingredients = tk.LabelFrame(self, text="Ingredients")
		bottom.add(ingredients)
		
		instructions = tk.LabelFrame(self, text="Instructions")
		bottom.add(instructions)
		
		adding = tk.Button(ingredients, text="Add Ingredient").grid(row=0, column=0)
		addinst = tk.Button(instructions, text="Add Instruction").grid(row=0, column=0)
		
		self.bind_all('<<ListboxSelect>>', getattr(self,'on_food_change'))
	
	def on_food_change(self, evt):
		try:
			val = evt.widget.get(int(evt.widget.curselection()[0]))
		except: # sometimes it decides to deselect and the tuple[0] fails
			return
		food = self.foodlist.get_food(val)
		self.config(text=food.name)
		for e in self.entries:
			e.set(food)
	
	
class FoodList(tk.Frame):
	def __init__(self, parent, foods, **kwargs):
		tk.Frame.__init__(self, parent, **kwargs)
		self.foods = foods
		
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		yScroll = tk.Scrollbar(self, orient=tk.VERTICAL)
		yScroll.grid(row=0, column=1, sticky=tk.N+tk.S)
		self.all = tk.Listbox(self, yscrollcommand=yScroll.set)#, selectmode=tk.SINGLE)
		self.all.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
		yScroll['command'] = self.all.yview
		
		for f in self.foods:
			self.all.insert(tk.END, f.name)

	def get_food(self, foodstr):
		for f in self.foods:
			if f.name == foodstr:
				return f
		return None


class FoodBrowser(tk.PanedWindow): 
	def __init__(self, dbname, **kwargs):
		tk.PanedWindow.__init__(self, None, **kwargs)
		self.dbname = dbname
		self.foods, self.name = DB.load(dbname)
		self.master.title(self.name)

		self.foodlist = FoodList(self, self.foods)
		self.add(self.foodlist)
		self.add(FoodView(self, self.foodlist))
	
	def save(self):
		self.name = DB.save(self.foods, self.dbname)
		self.master.title(self.name)
		

if __name__ == '__main__':
	db = 'db/food' if len(sys.argv) < 2 else sys.argv[1]
	app = FoodBrowser(db)
	app.grid(sticky=tk.NE + tk.SW)
	top = app.winfo_toplevel()
	top.rowconfigure(0, weight=1)
	top.columnconfigure(0, weight=1)
	menuBar = tk.Menu(top)
	top['menu'] = menuBar
	sub_file = tk.Menu(menuBar)
	menuBar.add_cascade(label='File', menu=sub_file)
	sub_file.add_command(label='Save', command=getattr(app, 'save'))
	sub_file.add_command(label='Quit', command=app.quit)
	app.mainloop()

