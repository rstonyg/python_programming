import pygame
import sys
import json
import os

pygame.init()

WIDTH = 800
HEIGHT = 900
LINE_WIDTH = 15
BOARD_ROWS = 3
BOARD_COLS = 3
SQUARE_SIZE = 200
CIRCLE_RADIUS = SQUARE_SIZE // 3
CIRCLE_WIDTH = 15
CROSS_WIDTH = 25
SPACE = SQUARE_SIZE // 4

BG_COLOR = (28, 170, 156)
LINE_COLOR = (23, 145, 135)
CIRCLE_COLOR = (239, 231, 200)
CROSS_COLOR = (66, 66, 66)
WHITE = (255, 255, 255)
DARK_GREEN = (10, 100, 80)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)

SCORES_FILE = 'tictactoe_scores.json'

def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, 'r') as f:
            return json.load(f)
    return {'player_wins': 0, 'computer_wins': 0, 'draws': 0}

def save_scores(scores):
    with open(SCORES_FILE, 'w') as f:
        json.dump(scores, f)

def draw_button(text, x, y, width, height, color, text_color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)
    text_surf = font_medium.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surf, text_rect)
    return pygame.Rect(x, y, width, height)

def is_button_pressed(button_rect, pos):
    return button_rect.collidepoint(pos)

def draw_menu(scores):
    screen.fill(BG_COLOR)
    title = font_large.render('TIC TAC TOE', True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    
    score_text = font_small.render(f"Player: {scores['player_wins']}  Computer: {scores['computer_wins']}  Draws: {scores['draws']}", True, WHITE)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 150))
    
    start_button = draw_button('PLAY', 250, 350, 300, 100, DARK_GREEN, WHITE)
    quit_button = draw_button('QUIT', 250, 500, 300, 100, DARK_GREEN, WHITE)
    
    pygame.display.update()
    return start_button, quit_button

def draw_board():
    board_offset_y = 100
    pygame.draw.line(screen, LINE_COLOR, (0, board_offset_y + SQUARE_SIZE), (WIDTH, board_offset_y + SQUARE_SIZE), LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (0, board_offset_y + 2 * SQUARE_SIZE), (WIDTH, board_offset_y + 2 * SQUARE_SIZE), LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (SQUARE_SIZE, board_offset_y), (SQUARE_SIZE, board_offset_y + 3 * SQUARE_SIZE), LINE_WIDTH)
    pygame.draw.line(screen, LINE_COLOR, (2 * SQUARE_SIZE, board_offset_y), (2 * SQUARE_SIZE, board_offset_y + 3 * SQUARE_SIZE), LINE_WIDTH)

def draw_figures(board):
    board_offset_y = 100
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col]:
                surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                surf.fill(BG_COLOR)
                
                if board[row][col] == 'O':
                    pygame.draw.circle(surf, CIRCLE_COLOR, (SQUARE_SIZE // 2, SQUARE_SIZE // 2), CIRCLE_RADIUS, CIRCLE_WIDTH)
                elif board[row][col] == 'X':
                    pygame.draw.line(surf, CROSS_COLOR, (SPACE, SPACE), (SQUARE_SIZE - SPACE, SQUARE_SIZE - SPACE), CROSS_WIDTH)
                    pygame.draw.line(surf, CROSS_COLOR, (SPACE, SQUARE_SIZE - SPACE), (SQUARE_SIZE - SPACE, SPACE), CROSS_WIDTH)
                
                screen.blit(surf, (col * SQUARE_SIZE, board_offset_y + row * SQUARE_SIZE))

def get_square_from_click(pos):
    x, y = pos
    if 100 <= y <= 700 and 0 <= x <= 600:
        row = (y - 100) // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col
    return None

def check_winner(board):
    for row in range(BOARD_ROWS):
        if board[row][0] == board[row][1] == board[row][2] != None:
            return board[row][0]
    for col in range(BOARD_COLS):
        if board[0][col] == board[1][col] == board[2][col] != None:
            return board[0][col]
    if board[0][0] == board[1][1] == board[2][2] != None:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != None:
        return board[0][2]
    return None

def is_board_full(board):
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] is None:
                return False
    return True

def get_empty_squares(board):
    empty = []
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] is None:
                empty.append((row, col))
    return empty

def minimax(board, depth, is_maximizing):
    winner = check_winner(board)
    if winner == 'X':
        return 10 - depth
    elif winner == 'O':
        return depth - 10
    elif is_board_full(board):
        return 0
    
    if is_maximizing:
        best_score = -float('inf')
        for row, col in get_empty_squares(board):
            board[row][col] = 'X'
            score = minimax(board, depth + 1, False)
            board[row][col] = None
            best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for row, col in get_empty_squares(board):
            board[row][col] = 'O'
            score = minimax(board, depth + 1, True)
            board[row][col] = None
            best_score = min(score, best_score)
        return best_score

def get_best_move(board):
    best_score = -float('inf')
    best_move = None
    
    for row, col in get_empty_squares(board):
        board[row][col] = 'X'
        score = minimax(board, 0, False)
        board[row][col] = None
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move

def draw_game_screen(board, scores, message=""):
    screen.fill(BG_COLOR)
    
    score_text = font_small.render(f"Player: {scores['player_wins']}  Computer: {scores['computer_wins']}  Draws: {scores['draws']}", True, WHITE)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))
    
    draw_board()
    draw_figures(board)
    
    if message:
        msg_surf = font_medium.render(message, True, WHITE)
        screen.blit(msg_surf, (WIDTH // 2 - msg_surf.get_width() // 2, 750))

def draw_end_screen(board, scores, result):
    screen.fill(BG_COLOR)
    
    if result == 'player':
        title = font_large.render('YOU WIN!', True, (0, 255, 0))
    elif result == 'computer':
        title = font_large.render('COMPUTER WINS!', True, (255, 0, 0))
    else:
        title = font_large.render("IT'S A DRAW!", True, WHITE)
    
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    
    score_text = font_medium.render(f"Player: {scores['player_wins']}  Computer: {scores['computer_wins']}  Draws: {scores['draws']}", True, WHITE)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 150))
    
    draw_board()
    draw_figures(board)
    
    play_button = draw_button('PLAY AGAIN', 200, 750, 200, 80, DARK_GREEN, WHITE)
    menu_button = draw_button('MENU', 450, 750, 200, 80, DARK_GREEN, WHITE)
    
    pygame.display.update()
    return play_button, menu_button

def game_loop():
    clock = pygame.time.Clock()
    scores = load_scores()
    
    while True:
        start_btn, quit_btn = draw_menu(scores)
        
        menu_running = True
        while menu_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if is_button_pressed(start_btn, pos):
                        menu_running = False
                    elif is_button_pressed(quit_btn, pos):
                        pygame.quit()
                        sys.exit()
            clock.tick(60)
        
        board = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
        player = 'O'
        game_over = False
        computer_delay = 0
        
        game_running = True
        while game_running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and not game_over and player == 'O':
                    pos = event.pos
                    sq = get_square_from_click(pos)
                    if sq:
                        row, col = sq
                        if board[row][col] is None:
                            board[row][col] = 'O'
                            winner = check_winner(board)
                            if winner == 'O':
                                game_over = True
                                result = 'player'
                                scores['player_wins'] += 1
                            elif is_board_full(board):
                                game_over = True
                                result = 'draw'
                                scores['draws'] += 1
                            else:
                                player = 'X'
                                computer_delay = 30
            
            if player == 'X' and not game_over:
                if computer_delay > 0:
                    computer_delay -= 1
                else:
                    best_move = get_best_move(board)
                    if best_move:
                        row, col = best_move
                        board[row][col] = 'X'
                        winner = check_winner(board)
                        if winner == 'X':
                            game_over = True
                            result = 'computer'
                            scores['computer_wins'] += 1
                        elif is_board_full(board):
                            game_over = True
                            result = 'draw'
                            scores['draws'] += 1
                        else:
                            player = 'O'
            
            draw_game_screen(board, scores, "Computer is thinking..." if player == 'X' and not game_over else "")
            pygame.display.update()
            
            if game_over:
                save_scores(scores)
                play_btn, menu_btn = draw_end_screen(board, scores, result)
                
                end_running = True
                while end_running:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            pos = event.pos
                            if is_button_pressed(play_btn, pos):
                                end_running = False
                                game_running = False
                            elif is_button_pressed(menu_btn, pos):
                                end_running = False
                                game_running = False
                                break
                    clock.tick(60)

game_loop()