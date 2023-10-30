import enum
from enum import Enum, auto
import tkinter as tk
import random
from PIL import Image, ImageTk

GRID_SIZE = 8
WINDOW_EDGE_SIZE = 512
WINDOW_PADDING = 64
IMAGE_EDGE_SIZE = (WINDOW_EDGE_SIZE // GRID_SIZE)


class TileType:
	BLANK = auto()
	UP = auto()
	RIGHT = auto()
	DOWN = auto()
	LEFT = auto()

	@classmethod
	def values(cls):
		return TileType.BLANK, TileType.UP, TileType.RIGHT, TileType.DOWN, TileType.LEFT


class TkApp(tk.Tk):
	def __init__(self):
		super().__init__()
		print("init")

		self.title("Wave function collapse test (or Wang tiles?)")
		self.geometry(f"{WINDOW_EDGE_SIZE + WINDOW_PADDING}x{WINDOW_EDGE_SIZE + WINDOW_PADDING}")

		self.tk_images = {
			TileType.BLANK: ImageTk.PhotoImage(Image.open("img/mountains/blank.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.UP: ImageTk.PhotoImage(Image.open("img/mountains/up.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.RIGHT: ImageTk.PhotoImage(Image.open("img/mountains/right.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.DOWN: ImageTk.PhotoImage(Image.open("img/mountains/down.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.LEFT: ImageTk.PhotoImage(Image.open("img/mountains/left.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		}

		self.frame = tk.Frame()
		self.frame.pack(expand=True)

		for i in range(GRID_SIZE * GRID_SIZE):
			r, c = divmod(i, GRID_SIZE)
			tk_label = tk.Label(
				self.frame,
				text=f"{r},{c}",
				image=self.tk_images.get(random.choice(TileType.values())),
				highlightthickness=1,
				width=IMAGE_EDGE_SIZE,
				height=IMAGE_EDGE_SIZE,
				bg="green"
			)
			tk_label.grid(row=r, column=c)
		self.frame.pack()

		self.update()

	def update(self):
		super().update()
		print("redraw")


class Tile(object):
	def __init__(self):
		pass


class TileGrid(object):
	def __init__(self):
		pass


if __name__ == "__main__":
	tkApp = TkApp()
	tkApp.mainloop()
