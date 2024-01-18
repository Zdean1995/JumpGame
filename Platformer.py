import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join

pygame.init()

pygame.display.set_caption("Platformer")

WIDTH, HEIGHT = 800, 1000  # int(pygame.display.Info().current_w / 1.2), int(pygame.display.Info().current_h / 1.2)
FPS = 60
PLAYER_VEL = 15
# PLAYER_MAX_SPEED = 50
LEFT, RIGHT = "left", "right"

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 2
    SPRITES = load_sprite_sheets("MainCharacters", "VirtualGuy", 32, 32, True)
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = LEFT
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.jump_height = 8
        self.sprite = None

    def jump(self):
        self.y_vel = -self.GRAVITY * self.jump_height
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy
        '''
        if self.rect.x < -self.rect.width:
            self.rect.x = WIDTH + self.rect.width
        if self.rect.x > WIDTH + self.rect.width:
            self.rect.x = -self.rect.width
        if self.rect.y < -self.rect.height:
            self.rect.y = HEIGHT + self.rect.height
        if self.rect.y > HEIGHT + self.rect.height:
            self.rect.y = -self.rect.height
        '''

    def hurt(self):
        self.hit = True
        self.hit_count = 0

    def move_left(self, vel):
        self.x_vel = -vel  # max(-vel, -PLAYER_MAX_SPEED)
        if self.direction != LEFT:
            self.direction = LEFT
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel  # min(vel, PLAYER_MAX_SPEED)
        if self.direction != RIGHT:
            self.direction = RIGHT
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.fall_count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_y):  # , offset_x):
        win.blit(self.sprite, (self.rect.x, self.rect.y - offset_y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_y):  # , offset_x):
        win.blit(self.image, (self.rect.x, self.rect.y - offset_y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 65):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def get_border():
    surface = get_block(96)
    image = pygame.Surface((96, 96), pygame.SRCALPHA)
    image.blit(surface, (0, 0))
    border = []
    for i in range(-96, (HEIGHT + 96) // 97):
        border.append((WIDTH - 30, i * 96))
        border.append((-66, i * 96))

    return border, image


def draw(win, background, bg_image, player, objects, border, border_block, offset_y, blocks):  # , offset_x):
    for tile in background:
        win.blit(bg_image, (tile[0], tile[1] - ((offset_y / 10) % bg_image.get_height())))
        #  win.blit(bg_image, tile)

    flip_it = True
    for block in border:
        if flip_it:
            win.blit(pygame.transform.rotate(border_block, 90), (block[0], block[1] - offset_y/2))
            flip_it = False
        else:
            win.blit(pygame.transform.rotate(border_block, 270), (block[0], block[1] - offset_y/2))
            flip_it = True
    for obj in objects:
        obj.draw(win, offset_y)  # , offset_x)
    for block in blocks:
        block.draw(win, offset_y)

    player.draw(win, offset_y)  # , offset_x)

    pygame.display.update()


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    if player.rect.x < 0:
        player.rect.x = 0
    elif player.rect.x > WIDTH - player.rect.width:
        player.rect.x = WIDTH - player.rect.width
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()
            collided_objects.append(obj)

    return collided_objects


def generate_blocks(blocks, block_size):
    blocks.clear()
    blocks = [
        Block(random.randrange(30, WIDTH - block_size + 30), (HEIGHT // 2 - block_size) - (block_size * (i + 1) * 3),
              block_size)
        for i in range(100)]
    return blocks


def handle_move(player, objects, blocks):
    all_objects = [*objects, *blocks]
    keys = pygame.key.get_pressed()
    player.x_vel = 0
    collide_left = collide(player, all_objects, -PLAYER_VEL)
    collide_right = collide(player, all_objects, PLAYER_VEL)

    if keys[pygame.K_a] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_d] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, all_objects, player.y_vel)

    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire":
            player.hurt()

    # if(player.x_vel > 0):
    #     player.x_vel -= 1
    # if(player.x_vel < 0):
    #     player.x_vel += 1
    # if keys[pygame.K_a]:
    #     player.move_left(PLAYER_VEL - player.x_vel)
    # if keys[pygame.K_d]:
    #     player.move_right(PLAYER_VEL + player.x_vel)


def main(win):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")
    border, border_block = get_border()
    scroll_speed = 5

    block_size = 96

    player = Player(WIDTH // 2, HEIGHT // 2 - block_size, 50, 50)
    fire = Fire(100, HEIGHT // 2 - block_size - 64, 16, 32)
    fire.on()
    floor = [Block(i * block_size, HEIGHT // 2 - block_size, block_size)
             for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    blocks = []
    blocks = generate_blocks(blocks, block_size)
    objects = [*floor]

    offset_x = 0
    offset_y = 0
    scroll_area_width = 200
    game_tick = 0

    run = True
    while run:
        clock.tick(FPS)
        game_tick += 1

        if player.rect.y - offset_y > HEIGHT:
            game_tick = 0
            offset_y = 0
            scroll_speed = 5
            player.rect.x = WIDTH // 2
            player.rect.y = HEIGHT // 2 - block_size
            blocks = generate_blocks(blocks, block_size)
            player.jump_height = 8

        if game_tick % 1000 == 0:
            scroll_speed += 1
            player.jump_height += 1
        offset_y -= scroll_speed

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS)
        fire.loop()
        handle_move(player, objects, blocks)
        draw(win, background, bg_image, player, objects, border, border_block, offset_y, blocks)  # , offset_x)

        if (((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0)
                or ((player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0)):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
