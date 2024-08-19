import socket
import pygame
from math import hypot


server_ip, server_port = 'localhost', 10000
my_name = 'Player_1'


WIDTH_WINDOW, HEIGHT_WINDOW = 1000, 900
colors = {'0':(255, 0, 0), '1':(0, 255, 0), '2':(0, 0, 255), '3':(255, 255, 0), '4':(255, 0, 255)}
my_r = 50
GRID_COLOR = 'grey50'


def find(data):
    otkr = None
    for i in range(len(data)):
        if data[i] == '<':
            otkr = i
        if data[i] == '>' and i != None:
            zakr = i
            res = data[otkr+1:zakr]
            return res
    return ''


def write_name(x, y, r, name):
    font = pygame.font.Font(None, r)
    text = font.render(name, True, (0, 0, 0))
    rect = text.get_rect(center=(x, y))
    screen.blit(text, rect)


def draw_opponents(data):
    for i in range(len(data)):
        j = data[i].split(' ')
        x = WIDTH_WINDOW // 2 + int(j[0])
        y = HEIGHT_WINDOW // 2 + int(j[1])
        r = int(j[2])
        c = colors[j[3]]
        pygame.draw.circle(screen, c, (x, y), r)
        if len(j) == 5: write_name(x, y, r, j[4])


class Me():
    def __init__(self, data):
        data = data.split()
        self.r = int(data[0])
        self.color = data[1]

    def update(self, new_r):
        self.r = new_r

    def draw(self):
        if self.r != 0:
            pygame.draw.circle(screen, colors[self.color], (WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2), self.r)
            write_name(WIDTH_WINDOW // 2, HEIGHT_WINDOW // 2, self.r, my_name)


class Grid():
    def __init__(self, screen):
        self.screen = screen
        self.x = 0
        self.y = 0
        self.start_size = 100
        self.size = self.start_size

    def update(self, s_x, s_y, L):
        self.size = self.start_size // L
        self.x = -self.size + (-s_x) % self.size
        self.y = -self.size + (-s_y) % self.size

    def draw(self):
        for i in range(WIDTH_WINDOW // self.size + 2):
            pygame.draw.line(self.screen,
                             GRID_COLOR,
                             [self.x + i * self.size, 0],
                             [self.x + i * self.size, HEIGHT_WINDOW],
                             1)
        for i in range(HEIGHT_WINDOW // self.size + 2):
            pygame.draw.line(self.screen,
                             GRID_COLOR,
                             [0, self.y + i * self.size],
                             [WIDTH_WINDOW, self.y + i * self.size],
                             1)


pygame.init()
screen = pygame.display.set_mode((WIDTH_WINDOW, HEIGHT_WINDOW))
pygame.display.set_caption('Spore. Act I')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.connect((server_ip, server_port))

sock.send(('.' + my_name + ' ' + str(WIDTH_WINDOW) + ' ' + str(HEIGHT_WINDOW) + '.').encode())
data = sock.recv(64).decode()

me = Me(data)
grid = Grid(screen)

v = (0, 0)
old_v = (0, 0)
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if pygame.mouse.get_focused():
        pos = pygame.mouse.get_pos()
        v = (pos[0] - WIDTH_WINDOW // 2, pos[1] - HEIGHT_WINDOW // 2)

        if hypot(v[0], v[1]) <= me.r:
            v = (0, 0)

    if v != old_v:
        old_v = v
        message = '<' + str(v[0]) + ',' + str(v[1]) + '>'
        sock.send(message.encode())

# Получение нового состояния поля
    try:
        data = sock.recv(2 ** 20)
    except:
        running = False
        continue
    data = data.decode()
    data = find(data)
    data = data.split(',')


# Обработка входящих сообщений и  отрисовка нового состояния поля
    if data != ['']:
        params = list(map(int, data[0].split(' ')))
        me.update(params[0])
        grid.update(params[1], params[2], params[3])
        screen.fill('gray25')
        grid.draw()
        draw_opponents(data[1:])
        me.draw()
        print(data)

    pygame.display.update()

pygame.quit()
