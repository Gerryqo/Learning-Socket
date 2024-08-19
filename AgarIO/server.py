import socket
import pygame
import random
from math import hypot
import time


server_ip, server_port = 'localhost', 10000
WIDTH_ROOM, HEIGHT_ROOM = 4000, 4000
WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW = 300, 300
colors = {'0':(255, 0, 0), '1':(0, 255, 0), '2':(0, 0, 255), '3':(255, 255, 0), '4':(255, 0, 255)}
FPS = 100
START_PLAYER_SIZE = 50
FOOD_SIZE = 15
MOBS_VALUE = 25
FOOD_VALUE = (WIDTH_ROOM * HEIGHT_ROOM) // 80000


def find(data):
    otkr = None
    for i in range(len(data)):
        if data[i] == '<':
            otkr = i
        if data[i] == '>' and otkr != None:
            zakr = i
            res = data[otkr+1:zakr]
            res = list(map(int, res.split(',')))
            return res
    return ''


class Food():
    def __init__(self, x, y, r, color):
        self.x = x
        self.y = y
        self.r = r
        self.color = color


class Player():
    def __init__(self, conn, addr, x, y, r, color):
        self.conn = conn
        self.addr = addr
        self.x = x
        self.y = y
        self.r = r
        self.color = color
        self.L = 1

        self.name = 'Dumb'
        self.width_window = 1000
        self.height_window = 800
        self.w_vision = 1000
        self.h_vision = 800

        self.errors = 0
        self.dead_score = 0
        self.ready = False
        self.abs_speed = 30 / (self.r ** 0.5)
        self.speed_x = 0
        self.speed_y = 0

    def set_options(self, data):
        data = data[1:-1].split(' ')
        self.name = data[0]
        self.width_window = int(data[1])
        self.height_window = int(data[2])
        self.w_vision = int(data[1])
        self.h_vision = int(data[2])


    def change_speed(self, v):
        if (v[0] == 0) and (v[1] == 0):
            self.speed_x = 0
            self.speed_y = 0
        else:
            lenv = hypot(v[0], v[1])
            v = (v[0] / lenv, v[1] / lenv)
            v = (v[0] * self.abs_speed, v[1] * self.abs_speed)
            self.speed_x = v[0]
            self.speed_y = v[1]

    def update(self):
        if self.x - self.r <= 0:
            if self.speed_x >= 0:
                self.x += self.speed_x
        else:
            if self.x + self.r >= WIDTH_ROOM:
                if self.speed_x <= 0:
                    self.x += self.speed_x
            else:
                self.x += self.speed_x

        if self.y - self.r <= 0:
            if self.speed_y >= 0:
                self.y += self.speed_y
        else:
            if self.y + self.r >= HEIGHT_ROOM:
                if self.speed_y <= 0:
                    self.y += self.speed_y
            else:
                self.y += self.speed_y

        if self.r != 0:
            self.abs_speed = 30 / (self.r ** 0.5)
        else:
            self.abs_speed = 0

        if self.r >= 100:
            self.r -= self.r / 12000

        if (self.r >= self.w_vision / 4) or (self.r >= self.h_vision / 4):
            if (self.w_vision <= WIDTH_ROOM) or (self.h_vision <= HEIGHT_ROOM):
                self.L *= 2
                self.w_vision = self.width_window * self.L
                self.h_vision = self.height_window * self.L
        if (self.r < self.w_vision / 8) and (self.r < self.h_vision / 8):
            if self.L > 1:
                self.L = self.L // 2
                self.w_vision = self.width_window * self.L
                self.h_vision = self.height_window * self.L


# Основной сокет

main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind((server_ip, server_port))
main_socket.setblocking(0)
main_socket.listen(5)

start = time.time()
pygame.init()
print(f"Runtime: {time.time() - start}")
screen = pygame.display.set_mode((WIDTH_SERVER_WINDOW, HEIGHT_SERVER_WINDOW))
clock = pygame.time.Clock()

players = [Player(None, None,
                  random.randint(0, WIDTH_ROOM),
                  random.randint(0, HEIGHT_ROOM),
                  START_PLAYER_SIZE,
                  str(random.randint(0, 4)))
           for i in range(MOBS_VALUE)]

food = [Food(random.randint(0, WIDTH_ROOM),
             random.randint(0, HEIGHT_ROOM),
             FOOD_SIZE,
             str(random.randint(0, 4)))
        for i in range(FOOD_VALUE)]

tick = -1
running = True

while running:
    tick += 1
    clock.tick(FPS)
    if tick == 200:
        tick = 0
        try:
            new_socket, addr = main_socket.accept()
            print(f'Подключился пользователь с IP {addr}')
            new_socket.setblocking(0)
            spawn = random.choice(food)
            new_player = Player(new_socket,
                                addr,
                                spawn.x,
                                spawn.y,
                                START_PLAYER_SIZE,
                                str(random.randint(0, 4)))
            food.remove(spawn)
            message = str(new_player.r) + ' ' + new_player.color
            new_player.conn.send(message.encode())
            players.append(new_player)
        except:
            pass

        for i in range(MOBS_VALUE - len(players)):
            if len(food) != 0:
                spawn = random.choice(food)
                players.append(Player(None, None,
                                      spawn.x,
                                      spawn.y,
                                      random.randint(50, 100),
                                      str(random.randint(0, 4))))
                food.remove(spawn)

        new_food = [Food(random.randint(0, WIDTH_ROOM),
                        random.randint(0, HEIGHT_ROOM),
                        FOOD_SIZE,
                        str(random.randint(0, 4)))
                    for i in range(FOOD_VALUE - len(food))]
        food = food + new_food

# считывание и обработка команд игроков
    for player in players:
        if player.conn != None:
            try:
                data = player.conn.recv(1024)
                data = data.decode()
                if (data[0] == '.') and (data[-1] == '.'):
                    player.ready = True
                    player.set_options(data)
                    player.conn.send((str(START_PLAYER_SIZE) + ' ' + player.color).encode())
                else:
                    data = find(data)
                    player.change_speed(data)
            except:
                pass
        else:
            if tick == 100:
                data = [random.randint(-100, 100), random.randint(-100, 100)]
                player.change_speed(data)
        player.update()

# что видит каждый игрок
    visible_balls = [[] for i in range(len(players))]
    for i in range(len(players)):
        for k in range(len(food)):
            dist_x = food[k].x - players[i].x
            dist_y = food[k].y - players[i].y
            if ((abs(dist_x) <= players[i].w_vision // 2 + food[k].r)
                    and
                    (abs(dist_y) <= players[i].h_vision // 2 + food[k].r)):
                if hypot(dist_x, dist_y) <= players[i].r:
                    players[i].r = hypot(players[i].r, food[k].r)
                    food[k].r = 0
                if (players[i].conn != None) and (food[k].r != 0):
                    x_ = str(round(dist_x / players[i].L))
                    y_ = str(round(dist_y / players[i].L))
                    r_ = str(round(food[k].r / players[i].L))
                    c_ = food[k].color
                    visible_balls[i].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_)

        for j in range(i + 1, len(players)):
            dist_x = players[j].x - players[i].x
            dist_y = players[j].y - players[i].y

            if ((abs(dist_x) <= players[i].w_vision // 2 + players[j].r)
                    and
                    (abs(dist_y) <= players[i].h_vision // 2 + players[j].r)):
                if (hypot(dist_x, dist_y) <= players[i].r and
                        players[i].r > 1.1 * players[j].r):
                    players[i].r = hypot(players[i].r, players[j].r)
                    players[j].r, players[j].speed_x, players[j].speed_y = 0, 0, 0

                if players[i].conn != None:
                    x_ = str(round(dist_x / players[i].L))
                    y_ = str(round(dist_y / players[i].L))
                    r_ = str(round(players[j].r / players[i].L))
                    c_ = players[j].color
                    n_ = players[j].name
                    if players[j].r >= 30 * players[i].L:
                        visible_balls[i].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_ + ' ' + n_)
                    else:
                        visible_balls[i].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_)

            if ((abs(dist_x) <= players[j].w_vision // 2 + players[i].r)
                    and
                    (abs(dist_y) <= players[j].h_vision // 2 + players[i].r)):
                if (hypot(dist_x, dist_y) <= players[j].r and
                        players[j].r > 1.1 * players[i].r):
                    players[j].r = hypot(players[j].r, players[i].r)
                    players[i].r, players[i].speed_x, players[i].speed_y = 0, 0, 0

                if players[j].conn != None:
                    x_ = str(round(-dist_x / players[j].L))
                    y_ = str(round(-dist_y / players[j].L))
                    r_ = str(round(players[i].r / players[j].L))
                    c_ = players[i].color
                    n_ = players[i].name
                    if players[i].r >= 30 * players[j].L:
                        visible_balls[j].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_ + ' ' + n_)
                    else:
                        visible_balls[j].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_)

# формируем ответ парам игроков
    answers = ['' for i in range(len(players))]
    for i in range(len(players)):
        r_ = str(round(players[i].r / players[i].L))
        x_ = str(round(players[i].x / players[i].L))
        y_ = str(round(players[i].y / players[i].L))
        L_ = str(players[i].L)
        visible_balls[i] = [r_ + ' ' + x_ + ' ' + y_ + ' ' + L_] + visible_balls[i]
        answers[i] = '<' + (','.join(visible_balls[i])) + '>'

# отправка нового состояния игрового поля
    for i in range(len(players)):
        if (players[i].conn != None) and (players[i].ready):
            try:
                players[i].conn.send(answers[i].encode())
                players[i].errors = 0
            except:
                players[i].errors += 1

# чистка списка от отвалившихся игроков
    for player in players:
        if player.r == 0:
            if player.conn != None:
                player.dead_score += 1
            else:
                player.dead_score += 300
        if (player.errors == 500) or (player.dead_score == 300):
            if player.conn != None:
                player.conn.close()
            players.remove(player)

    for m in food:
        if m.r == 0:
            food.remove(m)

# отрисовка комнаты
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


# отрисовка игроков
    screen.fill('BLACK')
    for player in players:
        x = round(player.x * WIDTH_SERVER_WINDOW / WIDTH_ROOM)
        y = round(player.y * HEIGHT_SERVER_WINDOW / HEIGHT_ROOM)
        r = round(player.r * WIDTH_SERVER_WINDOW / WIDTH_ROOM)
        c = colors[player.color]

        pygame.draw.circle(screen, c, (x, y), r)

    pygame.display.update()

pygame.quit()
main_socket.close()
