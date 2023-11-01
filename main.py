import typing

import math
import random
import tkinter as tk
import operator
from enum import Enum, auto
from typing import Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageTk

GRID_SIZE = 8
WINDOW_EDGE_SIZE = 512
WINDOW_PADDING = 8
IMAGE_EDGE_SIZE = (WINDOW_EDGE_SIZE // GRID_SIZE)


@dataclass
class Vec2:
	x: int
	y: int

	def __add__(self, other):
		match other:
			case int() | float():
				return Vec2(self.x + other, self.y + other)
			case Vec2(_, _):
				return Vec2(self.x + other.x, self.y + other.y)
			case _:
				raise RuntimeError(f"unknown type to operate with: {other}")

	def __mul__(self, other):
		match other:
			case int() | float():
				return Vec2(self.x * other, self.y * other)
			case Vec2(_, _):  # element-wise multiplication, not cross-product
				return Vec2(self.x * other.x, self.y * other.y)
			case _:
				raise RuntimeError(f"unknown type to operate with: {other}")

	def as_tuple(self):
		return self.x, self.y

	def __str__(self):
		return f"[{self.x}, {self.y}]"


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

	def get_edge_id(self, edge: TileEdge):
		match edge:
			case TileEdge.UP: return self.up
			case TileEdge.RIGHT: return self.right
			case TileEdge.DOWN: return self.down
			case TileEdge.LEFT: return self.left
			case _: raise RuntimeError(f"Unknown edge '{edge}'.")

	def __str__(self):
		return f"\u21bb: {self.up, self.right, self.down, self.left}"


@dataclass
class ProtoTile:
	image: Image
	image_tk: ImageTk.PhotoImage
	image_tk_mini: ImageTk.PhotoImage
	edges: TileEdges

	@classmethod
	def create(cls, image: Image, edges: TileEdges):
		return ProtoTile(
			image=image,
			image_tk=ImageTk.PhotoImage(image),
			image_tk_mini=ImageTk.PhotoImage(image.resize((IMAGE_EDGE_SIZE // 2, IMAGE_EDGE_SIZE // 2))),
			edges=edges
		)

	def make_copy(self):
		return ProtoTile(
			image=self.image,
			image_tk=self.image_tk,
			image_tk_mini=self.image_tk_mini,
			edges=deepcopy(self.edges)
		)

	def __str__(self):
		return f"{self.edges}"


class TileFactory(object):
	def __init__(self, image_dir: str, tile_image_size: int):
		self._image_dir = Path(image_dir)
		self._image_size = tile_image_size

	def generate_tiles(self, image_name: str, edges: TileEdges, transformations: tuple[TileTransformation] = None) -> Tuple[ProtoTile, ...]:
		image = Image.open(self._image_dir / image_name).resize((self._image_size, self._image_size))
		tiles = []

		# TODO: use transformations param
		for i in range(4):
			tiles.append(ProtoTile.create(image.rotate(i * 90), edges.make_rotate_left(i)))

		return tuple(tiles)


@dataclass
class TileState:
	position: Vec2
	available_tiles: list[ProtoTile]
	final_tile: Optional[ProtoTile]

	@classmethod
	def create(cls, position: Vec2, initial_tiles: Tuple[ProtoTile, ...]):
		return TileState(position=position, available_tiles=[t.make_copy() for t in initial_tiles], final_tile=None)

	def prune_available_tiles(self, required_edge_id: int, in_direction: TileEdge):
		self.available_tiles = [t for t in self.available_tiles if t.edges.get_edge_id(in_direction) == required_edge_id]

	def do_collapse(self):
		self.final_tile = random.choice(self.available_tiles)
		if self.final_tile is None:
			raise RuntimeError(f"Failed to collapse tile {self!s}.")
		self.available_tiles = []

	@property
	def is_collapsed(self):
		return self.final_tile is not None

	def __str__(self):
		return f"\u2316: {self.position}, #: {len(self.available_tiles)}, collapsed: {'y' if self.final_tile is not None else 'n'}"


class TileBoard(object):

	_POSITION_MOVE_UNSAFE = {
		TileEdge.UP: Vec2(-1, 0),
		TileEdge.RIGHT: Vec2(0, +1),
		TileEdge.DOWN: Vec2(+1, 0),
		TileEdge.LEFT: Vec2(0, -1),
	}

	_TILE_EDGE_CLAMP = {
		TileEdge.UP: TileEdge.DOWN,
		TileEdge.RIGHT: TileEdge.LEFT,
		TileEdge.DOWN: TileEdge.UP,
		TileEdge.LEFT: TileEdge.RIGHT,
	}

	def __init__(self, board_size: Vec2, tiles: Tuple[ProtoTile, ...]):
		self._board_size = board_size
		self._proto_tiles = tiles
		self._board = []

	def build(self):
		board_tile_count = self._board_size.x * self._board_size.y
		self._board = [TileState.create(Vec2(*divmod(i, self._board_size.x)), self._proto_tiles) for i in range(board_tile_count)]

		complete = False
		while not complete:
			least_available = self._find_tiles_with_least_available_tiles()

			if len(least_available) == 0:
				raise RuntimeError("No tiles found!")

			picked_tile = random.choice(least_available)
			# picked_tile = self._get_tile_on_position_safe(Vec2(1,1))
			picked_tile.do_collapse()

			# update neighbor tiles
			neighbors = {tileEdge: self._get_tile_in_direction(picked_tile, tileEdge) for tileEdge in TileEdge}
			print(neighbors)

			# TODO: update neighbor's available_tiles
			for tile_edge, neighbor in neighbors.items():
				if neighbor is not None:
					neighbor.prune_available_tiles(
						picked_tile.final_tile.edges.get_edge_id(tile_edge),
						TileBoard._TILE_EDGE_CLAMP[tile_edge]
					)

			complete = next((t for t in self._board if not t.is_collapsed), None) is None
		print(self._board)

	def _find_tiles_with_least_available_tiles(self) -> list[TileState]:
		histogram = defaultdict(list)
		for tile in self._board:
			if not tile.is_collapsed:
				histogram[len(tile.available_tiles)].append(tile)
		return histogram[min(histogram.keys())]

	def _get_tile_in_direction(self, pivot_tile: TileState, direction: TileEdge) -> Optional[TileState]:
		target_position = pivot_tile.position + TileBoard._POSITION_MOVE_UNSAFE[direction]
		return self._get_tile_on_position_safe(target_position)

	def _get_tile_on_position_safe(self, position: Vec2) -> Optional[TileState]:
		return self._board[position.y * self._board_size.x + position.x] \
			if 0 <= position.x < self._board_size.x and 0 <= position.y < self._board_size.y \
			else None

	def get_tiles(self) -> list[TileState]:
		return self._board


class TkApp(tk.Tk):
	def __init__(self):
		super().__init__()

		self.title("Wave function collapse test (or Wang tiles?)")
		self.canvas = tk.Canvas(
			self,
			width=(WINDOW_EDGE_SIZE + 0 * WINDOW_PADDING),
			height=(WINDOW_EDGE_SIZE + 0 * WINDOW_PADDING)
		)
		self.canvas.pack()
		# self.geometry(f"{WINDOW_EDGE_SIZE + WINDOW_PADDING}x{WINDOW_EDGE_SIZE + WINDOW_PADDING}")

		self._tile_factory = TileFactory("img/mountains", IMAGE_EDGE_SIZE)
		self.tiles = self._tile_factory.generate_tiles("down.png", TileEdges(0, 1, 1, 1))

		self.board = TileBoard(Vec2(GRID_SIZE, GRID_SIZE), self.tiles)
		self.build_board()
		self.update()

	def build_board(self):
		self.board.build()

	def update(self):
		super().update()

		for tile in self.board.get_tiles():
			if tile.final_tile is not None:
				self.canvas.create_image(
					*(tile.position * IMAGE_EDGE_SIZE).as_tuple(),
					anchor=tk.NW,
					image=tile.final_tile.image_tk
				)
			else:
				# draw first 4 available tiles
				pos_delta = Vec2(IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE) * 0.5
				for i, available_tile in enumerate(tile.available_tiles[:4]):
					r, c = divmod(i, 2)
					p = tile.position * IMAGE_EDGE_SIZE + Vec2(c, r) * pos_delta
					self.canvas.create_image(
						*p.as_tuple(),
						anchor=tk.NW,
						image=available_tile.image_tk_mini
					)


if __name__ == "__main__":
	tkApp = TkApp()
	tkApp.mainloop()
