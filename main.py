import enum
from enum import Enum, auto
import tkinter as tk
from dataclasses import dataclass
import random
from PIL import Image, ImageTk
from pathlib import Path

GRID_SIZE = 8
WINDOW_EDGE_SIZE = 512
WINDOW_PADDING = 8
IMAGE_EDGE_SIZE = (WINDOW_EDGE_SIZE // GRID_SIZE)


class TileEdge(Enum):
	UP = 0,  # y-
	RIGHT = 1,  # x+
	DOWN = 2,  # y+
	LEFT = 3,  # x-


class TileTransformation(Enum):
	ROTATE_BY_90_DEG_ALL_AROUND = auto(),
	# ROTATE_BY_180_DEG = auto(),
	# MIRROR_HORIZONTALLY = auto(),
	# MIRROR_VERTICALLY = auto(),
	# ROTATE_BY_90_DEG_ALL_AROUND_MIRRORED = auto(),
	# ROTATE_BY_180_DEG_MIRRORED = auto(),


@dataclass
class TileEdges:
	up: int
	right: int
	down: int
	left: int

	def make_rotate_left(self, amount: int):
		# https://stackoverflow.com/questions/5299135/how-to-efficiently-left-shift-a-tuple
		edges = (self.up, self.right, self.down, self.left)
		amount = amount % len(edges)
		return TileEdges(*(edges[amount:] + edges[0:amount]))


@dataclass
class ProtoTile:
	image: Image
	image_tk: ImageTk.PhotoImage
	edges: TileEdges

	@classmethod
	def create(cls, image: Image, edges: TileEdges):
		return ProtoTile(image=image, image_tk=ImageTk.PhotoImage(image), edges=edges)


class TileFactory(object):
	def __init__(self, image_dir: str, tile_image_size: int):
		self._image_dir = Path(image_dir)
		self._image_size = tile_image_size

	def generate_tiles(self, image_name: str, edges: TileEdges, transformations: tuple[TileTransformation] = None) -> tuple[ProtoTile]:
		image = Image.open(self._image_dir / image_name).resize((self._image_size, self._image_size))
		tiles = []

		for i in range(1, 4):
			tiles.append(ProtoTile.create(image.rotate(i * 90), edges.make_rotate_left(i)))

		return tuple(tiles)


"""
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
"""

# class TileBoard(object):


class TkApp(tk.Tk):
	def __init__(self):
		super().__init__()
		print("init")

		self._tile_factory = TileFactory("img/mountains", IMAGE_EDGE_SIZE)

		self.title("Wave function collapse test (or Wang tiles?)")
		self.canvas = tk.Canvas(
			self,
			width=(WINDOW_EDGE_SIZE + 0*WINDOW_PADDING),
			height=(WINDOW_EDGE_SIZE + 0*WINDOW_PADDING)
		)
		self.canvas.pack()
		# self.geometry(f"{WINDOW_EDGE_SIZE + WINDOW_PADDING}x{WINDOW_EDGE_SIZE + WINDOW_PADDING}")

		self.tiles = self._tile_factory.generate_tiles("down.png", TileEdges(0, 1, 1, 1))

		# self.tk_images = {
		# 	TileType.BLANK: ImageTk.PhotoImage(Image.open("img/mountains/blank.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		# 	TileType.UP: ImageTk.PhotoImage(Image.open("img/mountains/up.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		# 	TileType.RIGHT: ImageTk.PhotoImage(Image.open("img/mountains/right.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		# 	TileType.DOWN: ImageTk.PhotoImage(Image.open("img/mountains/down.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		# 	TileType.LEFT: ImageTk.PhotoImage(Image.open("img/mountains/left.png").resize((IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE))),
		# }

		# self.frame = tk.Frame()
		# self.frame.pack(expand=True)

		for i, tile in enumerate(self.tiles):
			print(f"{tile=}")
			self.canvas.create_image(i*(IMAGE_EDGE_SIZE + WINDOW_PADDING), 0, anchor=tk.NW, image=tile.image_tk)
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
