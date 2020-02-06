import logging
import hexgrid
from catan.pieces import PieceType

_cardinal_direction = ['NW', 'W', 'SW', 'SE', 'E', 'NE']

def droid_move(board_frame, board):
	
	p = input()
	print(board_frame.game.state)

	if board_frame.game.state.is_in_pregame():

		if board_frame.game.state.can_place_settlement():
			board_frame.droid_piece_click(PieceType.settlement, best_settlement_position_coord(board))
		elif board_frame.game.state.can_place_road():
			board_frame.droid_piece_click(PieceType.road, 72)
		else:
			print("Not getting in")

	board_frame.redraw()

def best_settlement_position_coord(board):

	for tile_id in range(1, 20):  # tiles go from 1-19

		for cdir in _cardinal_direction:

			return hexgrid.from_location(hexgrid.NODE, tile_id, direction=cdir)
