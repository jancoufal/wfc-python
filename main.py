import enum
from enum import Enum, auto
import tkinter as tk
import random
from PIL import Image, ImageTk
from pathlib import Path

GRID_SIZE = 8
WINDOW_EDGE_SIZE = 512
WINDOW_PADDING = 8
IMAGE_EDGE_SIZE = (WINDOW_EDGE_SIZE // GRID_SIZE)


class TileEdge(Enum):
	UP = "y-",
	RIGHT = "x+"
	DOWN = "y+"
	LEFT = "x-"


class ProtoTile(object):
	def __init__(self, image: Image):
		self._image = image
		self._neighbor_map = {e: set() for e in TileEdge}

	# set[object] == set[ProtoTile]
	def set_neighbor_map(self, neighbor_map: dict[TileEdge, set[object]]):
		self._neighbor_map = neighbor_map

	@property
	def image(self):
		return self._image

	def get_neighbor_map(self, tile_edge: TileEdge):
		return self._neighbor_map[tile_edge]


class TileFactory(object):

	@classmethod
	def create_5_set(cls, image_dir: Path, image_size: int):
		def gen_tile(_type):
			return ProtoTile(Image.open(image_dir / (_type + ".png")).resize((image_size, image_size)))

		b = gen_tile("blank")
		u = gen_tile("up")
		r = gen_tile("right")
		d = gen_tile("down")
		l = gen_tile("left")

		# define neighbors
		b.set_neighbor_map({
			TileEdge.UP: (b, u),
			TileEdge.RIGHT: (b, r),
			TileEdge.DOWN: (b, d),
			TileEdge.LEFT: (b, l),
		})

	def __init__(self, tiles: set):
		self._tiles = tiles


class Tile(object):
	def __init__(self, options: set):
		self._options = set(options)

	def is_collapsed(self):
		return len(self._options) == 1

	def is_out_of_options(self):
		return len(self._options) == 0

	def remove_options(self, options_to_remove: set):
		self._options = self._options - set(options_to_remove)

	def get_options(self) -> set:
		return self._options

	def get_collapsed_option(self):
		return tuple(self._options)[0] if self.is_collapsed() else None


# class TileBoard(object):

class TkApp(tk.Tk):
	def __init__(self):
		super().__init__()
		print("init")

		self.title("Wave function collapse test (or Wang tiles?)")
		self.canvas = tk.Canvas(
			self,
			width=(WINDOW_EDGE_SIZE + 0*WINDOW_PADDING),
			height=(WINDOW_EDGE_SIZE + 0*WINDOW_PADDING)
		)
		self.canvas.pack()
		# self.geometry(f"{WINDOW_EDGE_SIZE + WINDOW_PADDING}x{WINDOW_EDGE_SIZE + WINDOW_PADDING}")

		self.tk_images = {
			TileType.BLANK: ImageTk.PhotoImage(Image.open("img/mountains/blank.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.UP: ImageTk.PhotoImage(Image.open("img/mountains/up.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.RIGHT: ImageTk.PhotoImage(Image.open("img/mountains/right.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.DOWN: ImageTk.PhotoImage(Image.open("img/mountains/down.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
			TileType.LEFT: ImageTk.PhotoImage(Image.open("img/mountains/left.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		}

		# self.frame = tk.Frame()
		# self.frame.pack(expand=True)

		self.canvas.create_image(IMAGE_EDGE_SIZE, 0, anchor=tk.NW, image=self.tk_images.get(TileType.BLANK))
		# self.canvas.pack()

		# for i in range(GRID_SIZE * GRID_SIZE):
		# 	r, c = divmod(i, GRID_SIZE)
		# 	self.canvas.create_image(
		# 		r * IMAGE_EDGE_SIZE + WINDOW_PADDING,
		# 		c * IMAGE_EDGE_SIZE + WINDOW_PADDING,
		# 		image=self.tk_images.get(random.choice(list(TileType)))
		# 	)

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
