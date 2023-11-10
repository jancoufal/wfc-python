import logging
import tkinter
import typing
import math
import random
import tkinter as tk
import time
import operator
from enum import Enum, auto
from typing import Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy
from collections import defaultdict, deque
from pathlib import Path
from PIL import Image, ImageTk

DEBUG_MODE = True
GRID_SIZE = 8
WINDOW_EDGE_SIZE = 512 * 2
WINDOW_PADDING = 8
IMAGE_EDGE_SIZE = (WINDOW_EDGE_SIZE // GRID_SIZE)
LOGGING_CONFIG = {
	"level": logging.DEBUG,
	"format": "%(asctime)s - %(levelname)s : %(message)s",
	"datefmt": "%Y-%m-%d %H:%M:%S",
}


@dataclass
class Vec2i:
	x: int
	y: int

	def _do_operation(self, op, other):
		match other:
			case int() | float(): return Vec2i(op(self.x, other), op(self.y, other))
			case Vec2i(_, _): return Vec2i(op(self.x, other.x), op(self.y, other.y))
			case _: raise RuntimeError(f"unknown type to operate with: {other}")

	def __add__(self, other):
		return self._do_operation(operator.add, other)

	def __sub__(self, other):
		return self._do_operation(operator.sub, other)

	def __mul__(self, other):
		return self._do_operation(operator.mul, other)

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
	ORIGINAL = "orig"
	ROTATE_BY_90_DEG_CCW = "r1_ccw"
	ROTATE_BY_180_DEG_CCW = "r2_ccw"
	ROTATE_BY_270_DEG_CCW = "r3_ccw"


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
	name: str
	image: Image
	image_tk: ImageTk.PhotoImage
	image_tk_mini: ImageTk.PhotoImage
	edges: TileEdges

	@classmethod
	def create(cls, name: str, image: Image, edges: TileEdges):
		return ProtoTile(
			name=name,
			image=image,
			image_tk=ImageTk.PhotoImage(image),
			image_tk_mini=ImageTk.PhotoImage(image.resize((IMAGE_EDGE_SIZE // 3, IMAGE_EDGE_SIZE // 3))),
			edges=edges
		)

	def make_copy(self):
		return ProtoTile(
			name=self.name,
			image=self.image,
			image_tk=self.image_tk,
			image_tk_mini=self.image_tk_mini,
			edges=deepcopy(self.edges)
		)

	def __str__(self):
		return f"{self.edges}"


class TileFactory(object):

	_IMAGE_OPERATIONS = {
		TileTransformation.ORIGINAL: lambda img: img,
		TileTransformation.ROTATE_BY_90_DEG_CCW: lambda img: img.rotate(90),
		TileTransformation.ROTATE_BY_180_DEG_CCW: lambda img: img.rotate(180),
		TileTransformation.ROTATE_BY_270_DEG_CCW: lambda img: img.rotate(270),
	}

	_EDGE_OPERATION = {
		TileTransformation.ORIGINAL: lambda edges: edges,
		TileTransformation.ROTATE_BY_90_DEG_CCW: lambda edges: edges.make_rotate_left(1),
		TileTransformation.ROTATE_BY_180_DEG_CCW: lambda edges: edges.make_rotate_left(2),
		TileTransformation.ROTATE_BY_270_DEG_CCW: lambda edges: edges.make_rotate_left(3),
	}

	def __init__(self, image_dir: str, tile_image_size: int):
		self._image_dir = Path(image_dir)
		self._image_size = tile_image_size

	def generate_tiles(self, image_name: str, edges: TileEdges, transformations: tuple[TileTransformation]) -> Tuple[ProtoTile, ...]:
		image = Image.open(self._image_dir / image_name).resize((self._image_size, self._image_size))

		tiles = []
		for transformation in transformations:
			tiles.append(ProtoTile.create(
				f"{image_name}, {transformation.value}",
				TileFactory._IMAGE_OPERATIONS[transformation](image),
				TileFactory._EDGE_OPERATION[transformation](edges)
			))

		return tuple(tiles)


@dataclass
class TileState:
	iid: int
	position: Vec2i
	available_tiles: list[ProtoTile]

	@classmethod
	def create(cls, iid: int, position: Vec2i, initial_tiles: Tuple[ProtoTile, ...]):
		return TileState(iid, position, [t.make_copy() for t in initial_tiles])

	""" :return number of tiles pruned """
	def prune_available_tiles(self, required_edge_ids: set[int], in_direction: TileEdge) -> int:
		original_tile_count = len(self.available_tiles)
		self.available_tiles = [t for t in self.available_tiles if t.edges.get_edge_id(in_direction) in required_edge_ids]
		return original_tile_count - len(self.available_tiles)

	def do_collapse(self):
		if len(self.available_tiles) < 2:
			raise AssertionError(f"Tile '{self!s}' cannot be collapsed, no available tiles.")
		self.available_tiles = [random.choice(self.available_tiles)]

	@property
	def is_collapsed(self):
		return len(self.available_tiles) == 1

	@property
	def get_collapsed_tile(self):
		if not self.is_collapsed:
			raise AssertionError(f"Tile {self!s} is not collapsed.")
		return self.available_tiles[0]

	def __str__(self):
		return f"\u2316: {self.position}, #: {len(self.available_tiles)}, collapsed: {self.is_collapsed}"


class TileBoardEventListener(object):
	def __init__(self, logger: logging.Logger, canvas: tkinter.Canvas, canvas_size: Vec2i, tile_size: Vec2i, wait_hook: tkinter.IntVar):
		self._l = logger
		self._canvas = canvas
		self._canvas_size = canvas_size
		self._tile_size = tile_size
		self._wait_hook = wait_hook

	def on_start(self, board: list[TileState], board_size: Vec2i):
		self._l.info(f"on_start({board_size=}, {len(board)=})")
		self._draw_board(board)
		self._do_wait()

	def on_finish(self, board: list[TileState]):
		self._l.info(f"on_finish({len(board)=})")
		self._draw_board(board)

	def on_single_loop_start(self, board: list[TileState]):
		self._l.info(f"on_single_loop_start()")

	def on_single_loop_end(self, board: list[TileState]):
		self._l.info(f"on_single_loop_end()")

	def on_find_tiles_with_least_available_tiles(self, board: list[TileState], tiles: list[TileState]):
		self._l.info(f"on_find_tiles_with_least_available_tiles({len(tiles)=})")

	def on_random_tile_picked(self, board: list[TileState], tile: TileState):
		self._l.info(f"on_random_tile_picked({tile=!s})")

	def on_tile_collapse(self, board: list[TileState], tile: TileState):
		self._l.info(f"on_tile_collapse({tile=!s})")
		self._draw_board(board)
		self._draw_tile(tile, "lime")
		self._do_wait()

	def on_neighbor_propagate_start(self, board: list[TileState], tile: TileState, back_trace: deque[TileState]):
		self._l.info(f"on_neighbor_propagate_start({tile=!s}, {len(back_trace)=})")
		self._draw_board(board)
		self._draw_tile(tile, "cyan")
		self._draw_backtrace(back_trace)
		self._do_wait()

	def on_neighbor_tiles_pruned(self, board: list[TileState], tile: TileState, number_of_pruned_tiles: int, back_trace: deque[TileState]):
		self._l.info(f"on_neighbor_tiles_pruned({tile=!s}, {number_of_pruned_tiles=}, {len(back_trace)=})")
		self._draw_board(board)
		self._draw_tile(tile, "red")
		self._draw_backtrace(back_trace)
		self._do_wait()

	def on_neighbor_propagate_finish(self, board: list[TileState], tile: TileState, back_trace: deque[TileState]):
		self._l.info(f"on_neighbor_propagate_finish({tile=!s}, {len(back_trace)=})")
		self._draw_board(board)
		self._draw_tile(tile, "gray")
		self._draw_backtrace(back_trace)
		self._do_wait()

	def _draw_board(self, board: list[TileState]):
		self._canvas.delete("all")
		for tile in board:
			self._draw_tile(tile)

	def _draw_tile(self, tile: TileState, outline=None):
		self._draw_tile_collapsed(tile) if tile.is_collapsed else self._draw_tile_superposition(tile)
		if outline is not None:
			self._canvas.create_rectangle(
				*(tile.position * self._tile_size).as_tuple(),
				*((tile.position + Vec2i(1, 1)) * self._tile_size - Vec2i(1, 1)).as_tuple(),
				# fill="green",
				outline=outline
			)

	def _draw_tile_collapsed(self, tile: TileState):
		self._canvas.create_image(
			*(tile.position * self._tile_size).as_tuple(),
			anchor=tk.NW,
			image=tile.get_collapsed_tile.image_tk
		)

	def _draw_tile_superposition(self, tile: TileState):
		# draw first 9 available tiles
		pos_delta = self._tile_size * 0.33
		for i, available_tile in enumerate(tile.available_tiles[:9]):
			r, c = divmod(i, 3)
			p = tile.position * self._tile_size + Vec2i(c, r) * pos_delta
			self._canvas.create_image(
				*p.as_tuple(),
				anchor=tk.NW,
				image=available_tile.image_tk_mini
			)

	def _draw_backtrace(self, back_trace: deque[TileState]):
		prev_point = None
		for tile in back_trace:
			point = tile.position * self._tile_size + self._tile_size * 0.5
			if prev_point is not None:
				self._canvas.create_line(*prev_point.as_tuple(), *point.as_tuple(), fill="red", width=3)
			prev_point = point

	def _do_wait(self):
		if self._wait_hook is not None:
			self._canvas.wait_variable(self._wait_hook)
		self._canvas.update()


class TileBoard(object):

	_POSITION_MOVE_UNSAFE = {
		TileEdge.UP: Vec2i(0, -1),
		TileEdge.RIGHT: Vec2i(+1, 0),
		TileEdge.DOWN: Vec2i(0, +1),
		TileEdge.LEFT: Vec2i(-1, 0),
	}

	_TILE_EDGE_OPPOSITE = {
		TileEdge.UP: TileEdge.DOWN,
		TileEdge.RIGHT: TileEdge.LEFT,
		TileEdge.DOWN: TileEdge.UP,
		TileEdge.LEFT: TileEdge.RIGHT,
	}

	def __init__(self, board_size: Vec2i, tiles: Tuple[ProtoTile, ...], event_listener: TileBoardEventListener):
		self._board_size = board_size
		self._proto_tiles = tiles
		self._board = []
		self._event_listener = event_listener

	def build(self):
		board_tile_count = self._board_size.x * self._board_size.y
		self._board = [TileState.create(i, Vec2i(*(divmod(i, self._board_size.x)[::-1])), self._proto_tiles) for i in range(board_tile_count)]

		self._event_listener.on_start(self._board, self._board_size)

		complete = False
		step_counter = 0
		try:
			while not complete:
				self._event_listener.on_single_loop_start(self._board)

				least_available = self._find_tiles_with_least_available_tiles()
				self._event_listener.on_find_tiles_with_least_available_tiles(self._board, least_available)

				if len(least_available) == 0:
					raise RuntimeError("No tiles found!")

				picked_tile = random.choice(least_available)
				# picked_tile = self._get_tile_on_position_safe(Vec2(1,1))
				self._event_listener.on_random_tile_picked(self._board, picked_tile)

				picked_tile.do_collapse()
				self._event_listener.on_tile_collapse(self._board, picked_tile)

				self._propagate(picked_tile)

				complete = next((t for t in self._board if not t.is_collapsed), None) is None
				step_counter += 1

				self._event_listener.on_single_loop_end(self._board)

			logging.info(f"board finished in {step_counter} steps")
		except Exception as e:
			logging.error(e)

	def _propagate(self, tile: TileState):
		self._propagate_impl(tile, deque([tile]))

	def _propagate_impl(self, tile: TileState, back_trace: deque[TileState]):

		if len(tile.available_tiles) == 1 and not tile.is_collapsed:
			tile.do_collapse()
			self._event_listener.on_tile_collapse(self._board, tile)

		for tile_edge in TileEdge:
			neighbor_tile = self._get_tile_in_direction(tile, tile_edge)
			if neighbor_tile is not None and neighbor_tile not in back_trace:
				back_trace.append(neighbor_tile)
				self._event_listener.on_neighbor_propagate_start(self._board, neighbor_tile, back_trace)
				number_of_pruned_tiles = neighbor_tile.prune_available_tiles(
					set([e.edges.get_edge_id(tile_edge) for e in tile.available_tiles]),
					TileBoard._TILE_EDGE_OPPOSITE[tile_edge]
				)
				self._event_listener.on_neighbor_tiles_pruned(self._board, neighbor_tile, number_of_pruned_tiles, back_trace)
				if number_of_pruned_tiles > 0:
					self._propagate_impl(neighbor_tile, back_trace)
				back_trace.pop()
				self._event_listener.on_neighbor_propagate_finish(self._board, neighbor_tile, back_trace)

	def _find_tiles_with_least_available_tiles(self) -> list[TileState]:
		histogram = defaultdict(list)
		for tile in self._board:
			if not tile.is_collapsed:
				histogram[len(tile.available_tiles)].append(tile)
		return histogram[min(histogram.keys())]

	def _get_tile_in_direction(self, pivot_tile: TileState, direction: TileEdge) -> Optional[TileState]:
		target_position = pivot_tile.position + TileBoard._POSITION_MOVE_UNSAFE[direction]
		neighbor_tile = self._get_tile_on_position_safe(target_position)
		return neighbor_tile if neighbor_tile is not None and not neighbor_tile.is_collapsed else None

	def _get_tile_on_position_safe(self, position: Vec2i) -> Optional[TileState]:
		return self._board[position.x + position.y * self._board_size.x] \
			if 0 <= position.x < self._board_size.x and 0 <= position.y < self._board_size.y \
			else None

	def get_tiles(self) -> list[TileState]:
		return self._board


class TkApp(tk.Tk):
	def __init__(self):
		super().__init__()

		self._tk_click_event = tk.IntVar()
		self.bind("<Escape>", lambda _: self.destroy())
		self.bind("<KeyRelease>", self.on_key_release)

		self.title("Wave function collapse test (or Wang tiles?)")
		self.canvas_size = Vec2i(WINDOW_EDGE_SIZE + 0 * WINDOW_PADDING, WINDOW_EDGE_SIZE + 0 * WINDOW_PADDING)
		self.canvas = tk.Canvas(self, width=self.canvas_size.x, height=self.canvas_size.y)
		self.canvas.pack()
		self.canvas.bind("<Button-1>", self.on_canvas_click)

		self._tile_factory = TileFactory("img/mountains", IMAGE_EDGE_SIZE)
		self.tiles = []
		self.tiles.extend(self._tile_factory.generate_tiles("down.png", TileEdges(0, 1, 1, 1), tuple(e for e in TileTransformation)))
		self.tiles.extend(self._tile_factory.generate_tiles("blank.png", TileEdges(0, 0, 0, 0), (TileTransformation.ORIGINAL,)))

		self.event_listener = TileBoardEventListener(
			logging.getLogger("TkApp"),
			self.canvas,
			self.canvas_size,
			Vec2i(IMAGE_EDGE_SIZE, IMAGE_EDGE_SIZE),
			None  # self._tk_click_event
		)

		self.board = TileBoard(Vec2i(GRID_SIZE, GRID_SIZE), tuple(self.tiles), self.event_listener)
		self.build_board()
		self.update()

	def on_canvas_click(self, event):
		logging.debug(f"on_canvas_click: {event=}")
		self._tk_click_event.set(1)

	def on_key_release(self, event):
		logging.debug(f"on_key_release: {event=}")
		match event.char:
			case 'q': self.quit()
			case 'x': self._tk_click_event.set(1)

	def build_board(self):
		self.board.build()

	def update(self):
		super().update()


if __name__ == "__main__":
	logging.basicConfig(**LOGGING_CONFIG)
	random.seed(1)
	tkApp = TkApp()
	tkApp.mainloop()
	logging.info("done")
