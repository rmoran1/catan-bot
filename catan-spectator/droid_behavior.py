import logging

def droid_move(board_frame, board):

	logging.debug("DROID IS NOW MAKING ITS MOVE")
	
	if board_frame.game.state.can_place_settlement():
		logging.debug("PLACING SETTLEMENT")
		board_frame.game.place_settlement(39)
	elif board_frame.game.state.can_place_road():
		logging.debug("PLACING ROAD")
		board_frame.game.place_road(72)
		
	board_frame.redraw()
