import logging
import hexgrid
from catan.pieces import PieceType

_node_directions = ['NW', 'N', 'NE', 'SE', 'S', 'SW']
_edge_directions = ['NW', 'NE', 'E', 'SE', 'SW', 'W']

def droid_move(board_frame, board):
	
	p = input()
	print(board_frame.game.state)

	if board_frame.game.state.is_in_pregame():

		if board_frame.game.state.can_place_settlement():
			board_frame.droid_piece_click(PieceType.settlement, best_settlement_coord(board))
		elif board_frame.game.state.can_place_road():
			board_frame.droid_piece_click(PieceType.road, best_road_coord(board))

	board_frame.redraw()

def best_settlement_coord(board):

	for tile_id in range(1, 20):  # tiles go from 1-19

		for cdir in _node_directions:

			coord = hexgrid.from_location(hexgrid.NODE, tile_id, direction=cdir)

			if is_settlement_taken(board, coord):

				continue

			return coord

def best_road_coord(board):

	for tile_id in range(1, 20):  # tiles go from 1-19

		for cdir in _edge_directions:

			coord = hexgrid.from_location(hexgrid.EDGE, tile_id, direction=cdir)

			if is_road_taken(board, coord):

				continue

			return coord


def is_road_taken(board, coord):

	if (hexgrid.EDGE, coord) in board.pieces:
		return True
	return False

def is_settlement_taken(board, coord):

	if (hexgrid.NODE, coord) in board.pieces:
		return True
	return False
