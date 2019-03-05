#-*- coding:utf-8 -*-

import curses
from random import randrange, choice # generate and place new tile
from collections import defaultdict

# 定义用户动作
actions = ['Up','Left','Down','Right','Restart','Exit']
# 取每个key 对应的序列号 来做每个action的键 也就是大小写状态都适用
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
# {87: 'Up', 65: 'Left', 83: 'Down', 68: 'Right', 82: 'Restart', 81: 'Exit', 119: 'Up', 97: 'Left', 115: 'Down', 100: 'Right', 114: 'Restart', 113: 'Exit'}
actions_dict = dict(zip(letter_codes, actions * 2))

def get_user_action(keyboard): 
    ''' 阻塞用户输入，知道用户输入正确的值 '''   
    char = "N"
    while char not in actions_dict:    
        char = keyboard.getch()
    return actions_dict[char]

def transpose(field):
    ''' 矩阵转置 结果为原矩阵的转置 '''
    ''' a = [1,2,3]
        b = [4,5,6]
        c = [4,5,6,7,8]
        zipped = zip(a,b)     # 打包为元组的列表
        [(1, 4), (2, 5), (3, 6)]
        zip(a,c)              # 元素个数与最短的列表一致
        [(1, 4), (2, 5), (3, 6)]
        zip(*zipped)          # 与 zip 相反，可理解为解压，返回二维矩阵式
        [(1, 2, 3), (4, 5, 6)] zip(*field) 即为矩阵的转置'''
    return [list(row) for row in zip(*field)]

def invert(field):
    ''' 矩阵的逆转 对每一个row进行反转 生成新的field '''
    return [row[::-1] for row in field]

class GameField(object):
    ''' 棋盘类 初始化及相关游戏动作 '''
    def __init__(self,width=4, height=4, win_value=2048):
        self.width = width
        self.height = height
        self.win_value = win_value  #过关条件值
        self.score = 0  #当前分数
        self.highscore = 0  #最高分
        self.reset()  # 重置

    def spawn(self):
        ''' 随机生成新的数字2 4 2的几率9倍于4的几率 '''
        new_element = 4 if randrange(100) > 89 else 2
        # choice() 随机找一个位置并且该位置为空时 插入新元素
        (i,j) = choice([(i,j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element
    
    def reset(self):
        ''' 重置棋盘 '''
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        # 全部位置重新置为0
        self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        # 生成初始数字
        self.spawn()
        self.spawn()

    def move(self, direction):
        ''' 移动的函数列表 '''
        def move_row_left(row):
            def tighten(row): # 把零散的非零单元挤到一块
                new_row = [i for i in row if i != 0]
                new_row += [0 for i in range(len(row) - len(new_row))]
                return new_row

            def merge(row): # 对邻近元素进行合并
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row
            #先挤到一块再合并再挤到一块
            return tighten(merge(tighten(row)))

        #一行向左合并
        moves = {}
        moves['Left']  = lambda field: [move_row_left(row) for row in field]
        # 左右逆转[2,2,,0,0] 先逆转变成[0,0,2,2] 向左移动 [4,0,0,0] 再逆转[0,0,0,4] 即为想右移动的结果
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))

        moves['Up']    = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down']  = lambda field: transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                # 真正执行 用户动作的地方
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    def is_win(self):
        ''' 任何一个坐标的值大于 win_value 即获胜'''
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        ''' 任何位置都无法进行移动 游戏结束 '''
        return not any(self.move_is_possible(move) for move in actions)


    def move_is_possible(self, direction):
        def row_is_left_movable(row): 
            def change(i):
                if row[i] == 0 and row[i + 1] != 0: # 可以移动
                    return True
                if row[i] != 0 and row[i + 1] == row[i]: # 可以合并
                    return True
                return False
            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left']  = lambda field: any(row_is_left_movable(row) for row in field)

        check['Right'] = lambda field: check['Left'](invert(field))

        check['Up']    = lambda field: check['Left'](transpose(field))

        check['Down']  = lambda field: check['Right'](transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False
    def draw(self, screen):
        ''' 绘制棋盘 '''
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '          YOU WIN!'
        def cast(string):
            screen.addstr(string + '\n')

        #绘制水平分割线
        def draw_hor_separator():
            line = '+' + ('+------' * self.width + '+')[1:]
            separator = defaultdict(lambda: line)
            # 判断是否存在属性 counter 不存在则添加一个
            if not hasattr(draw_hor_separator, "counter"):
                draw_hor_separator.counter = 0
            # 以counter为key value为水平分割线到 separator 中
            cast(separator[draw_hor_separator.counter])
            draw_hor_separator.counter += 1
        
        #绘制竖直分割线及各单位field
        def draw_row(row):
            ''' 每一个竖线后面接一个field 若为0 则以中对齐宽度为5填充空格 一共画4次'''
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()

        cast('SCORE: ' + str(self.score))
        if 0 != self.highscore:
            cast('HIGHSCORE: ' + str(self.highscore))

        for row in self.field:
            draw_hor_separator()
            draw_row(row)

        draw_hor_separator()

        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)

def main(stdscr):
    ''' 游戏的主逻辑 '''

    #生成棋盘类 并对棋盘做相关初始化 及 结束 重启动作
    game_field = GameField(win_value=2048)

    def init():
        #重置游戏棋盘
        game_field.reset()
        return 'Game'

    def not_game(state):
        #画出 GameOver 或者 Win 的界面
        game_field.draw(stdscr)
        #读取用户输入得到action，判断是重启游戏还是结束游戏
        action = get_user_action(stdscr)
        responses = defaultdict(lambda: state) #默认是当前状态，没有行为就会一直在当前界面循环
        responses['Restart'], responses['Exit'] = 'Init', 'Exit' #对应不同的行为转换到不同的状态
        return responses[action]

    def game():
        #画出当前棋盘状态
        game_field.draw(stdscr)
        #读取用户输入得到action 如果为 用户行为 则一直在游戏界面
        action = get_user_action(stdscr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action): # move successful
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'


    state_actions = {
            'Init': init,
            'Win': lambda: not_game('Win'),
            'Gameover': lambda: not_game('Gameover'),
            'Game': game
        }

    curses.start_color()


    state = 'Init'

    #状态机开始循环
    while state != 'Exit':
        state = state_actions[state]()

if __name__ == '__main__':

    curses.wrapper(main)

    

    
    


