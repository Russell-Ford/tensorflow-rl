import numpy as np

class connect4:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[0]*7 for _ in xrange(6)]
        self.p1_board = np.empty([6,7], dtype=np.bool)
        self.p2_board = np.empty_like(self.p1_board)
        self.p1_board[:] = False
        self.p2_board[:] = False
        self.p1_turn = True
        self.moveNum = 1
        self.terminal = False

    def getPlayersMove(self):
        move = -1
        while(move < 0) or (move > 6):
            move = int(raw_input("Column 0-6 (sorry I'm a programmer): "))
            if not self.inputMove(move):
                move = -1

    def apply_action(self, move):
        if(move < 0) or (move > 6):
            print("invalid move :(( ", move)
            return -1, self.terminal
        if self.p1_turn:
            currentPlayer = 1
        else:
            currentPlayer = -1
        row = 5
        while(row > -1):
            if(self.board[row][move] == 0):
                self.board[row][move] = currentPlayer
                self.moveNum += 1
                if(currentPlayer == 1):
                    self.p1_board[row][move] = True
                else:
                    self.p2_board[row][move] = True
                if self.checkWin(row, move):
                    self.terminal = True
                    #if currentPlayer:
                    #    print("Player 1 won!")
                    #else:
                    #    print("Player 2 won!")
                    return 1, self.terminal
                if self.checkTie():
                    self.terminal = True
                    return 0, self.terminal
                return 0, self.terminal
            row -= 1
        print("invalid move :( ", move)
        self.printBoard()
        return -1, self.terminal

    def printBoard(self):
        for row in range(0,6):
            print(self.board[row])

    def checkTie(self):
        if self.moveNum >= 42:
            return True

    def checkWin(self, row, col):
        if self.p1_turn:
            currentPlayer = 1
        else:
            currentPlayer = -1
        score = 0
        lastMove = (row,col)
        #downward check
        while(row < 6):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            row += 1
        if(score > 3):
            self.terminal = True
            return True
        
        score = 0
        row = lastMove[0]

        #horizontal check
        while(col > -1):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            col -= 1
        #here we set col 1 past where the last move was made so we don't count it twice
        col = lastMove[1] + 1
        while(col < 7):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            col += 1
        if(score > 3):
            self.terminal = True
            return True

        score = 0
        col = lastMove[1]
        #up-left, down-right diagonal check
        while(row > -1 and col > -1):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            col -= 1
            row -= 1
        row = lastMove[0] + 1
        col = lastMove[1] + 1
        while(row < 6 and col < 7):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            col += 1
            row += 1
        if(score > 3):
            self.terminal = True
            return True

        score = 0
        row = lastMove[0]
        col = lastMove[1]
        #up-right, down-left diagonal check
        while(row > -1 and col < 7):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            col += 1
            row -= 1
        row = lastMove[0] + 1
        col = lastMove[1] - 1
        while(row < 6 and col > -1):
            if(self.board[row][col] == currentPlayer):
                score += 1
            else:
                break
            col -= 1
            row += 1
        if(score > 3):
            self.terminal = True
            return True

        return False

#def main():
#    test = connect4()
#    while(test.terminal == False):
#        for row in range(0,6):
#            print(test.board[row])
#        test.getPlayersMove()
#
#if __name__ == '__main__':
#    main()
