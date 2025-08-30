import math
import os
from random import randint
from collections import deque

import pygame
from pygame.locals import *


FPS = 60
ANIMATION_SPEED = 0.18
WIN_WIDTH = 284 * 2
WIN_HEIGHT = 512


class Bird(pygame.sprite.Sprite):
    WIDTH = HEIGHT = 32
    GRAVITY = 0.00007
    JUMP_VELOCITY = -0.1

    def __init__(self, x, y, msec_to_climb, images):
        super(Bird, self).__init__()
        self.x, self.y = x, y
        self.velocity = 0.0
        self.energy = 1.0 
        self._img_wingup, self._img_wingdown = images
        self._mask_wingup = pygame.mask.from_surface(self._img_wingup)
        self._mask_wingdown = pygame.mask.from_surface(self._img_wingdown)

    def update(self, delta_frames=1):
        time = frames_to_msec(delta_frames)
        self.velocity += Bird.GRAVITY * time
        self.y += self.velocity * time

        drain_per_sec = 1 / 100
        self.energy -= drain_per_sec * (time / 1000.0)
        self.energy = max(0.0, self.energy)

    def flap(self):
        if self.energy > 0.05:
            self.velocity = Bird.JUMP_VELOCITY
            self.energy -= 1 / 20 
            self.energy = max(0.0, self.energy)

    def regen_energy(self, amount):
        self.energy = min(1.0, self.energy + amount)

    @property
    def image(self):
        if pygame.time.get_ticks() % 500 >= 250:
            return self._img_wingup
        else:
            return self._img_wingdown

    @property
    def mask(self):
        if pygame.time.get_ticks() % 500 >= 250:
            return self._mask_wingup
        else:
            return self._mask_wingdown

    @property
    def rect(self):
        return Rect(self.x, self.y, Bird.WIDTH, Bird.HEIGHT)


class PipePair(pygame.sprite.Sprite):
    WIDTH = 80
    PIECE_HEIGHT = 32
    ADD_INTERVAL = 3000

    def __init__(self, pipe_end_img, pipe_body_img):
        super().__init__() 
        self.x = float(WIN_WIDTH - 1)
        self.score_counted = False


        self.image = pygame.Surface((PipePair.WIDTH, WIN_HEIGHT), SRCALPHA)
        self.image.convert()
        self.image.fill((0, 0, 0, 0))

        total_pipe_body_pieces = int(
            (WIN_HEIGHT - 3 * Bird.HEIGHT - 3 * PipePair.PIECE_HEIGHT) /
            PipePair.PIECE_HEIGHT
        )
        self.bottom_pieces = randint(1, total_pipe_body_pieces)
        self.top_pieces = total_pipe_body_pieces - self.bottom_pieces

        for i in range(1, self.bottom_pieces + 1):
            piece_pos = (0, WIN_HEIGHT - i * PipePair.PIECE_HEIGHT)
            self.image.blit(pipe_body_img, piece_pos)
        bottom_pipe_end_y = WIN_HEIGHT - self.bottom_height_px
        bottom_end_piece_pos = (0, bottom_pipe_end_y - PipePair.PIECE_HEIGHT)
        self.image.blit(pipe_end_img, bottom_end_piece_pos)


        for i in range(self.top_pieces):
            self.image.blit(pipe_body_img, (0, i * PipePair.PIECE_HEIGHT))
        top_pipe_end_y = self.top_height_px
        self.image.blit(pipe_end_img, (0, top_pipe_end_y))

        self.top_pieces += 1
        self.bottom_pieces += 1

        self.rect = self.image.get_rect()
        self.rect.x = int(self.x)
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def top_height_px(self):
        return self.top_pieces * PipePair.PIECE_HEIGHT

    @property
    def bottom_height_px(self):
        return self.bottom_pieces * PipePair.PIECE_HEIGHT

    @property
    def visible(self):
        return -PipePair.WIDTH < self.x < WIN_WIDTH

    def update(self, delta_frames=1):
        self.x -= ANIMATION_SPEED * frames_to_msec(delta_frames)
        self.rect.x = int(self.x) 

    def collides_with(self, bird):
        return pygame.sprite.collide_mask(self, bird)


class Rocket(pygame.sprite.Sprite):
    SPEED = 0.35
    ADD_INTERVAL = 5000

    def __init__(self, rocket_img, y, target_x):
        super(Rocket, self).__init__()
        self.image = rocket_img
        self.x = WIN_WIDTH
        self.y = y
        self.target_x = target_x
        self.mask = pygame.mask.from_surface(self.image)
        self.triggered = False

    @property
    def rect(self):
        return Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

    def update(self, delta_frames=1):
        self.x -= Rocket.SPEED * frames_to_msec(delta_frames)

    def check_trigger(self, bird):
        if not self.triggered and self.x <= self.target_x:
            self.triggered = True
            return self.rect.colliderect(bird.rect)
        return False


class Heart(pygame.sprite.Sprite):
    SPEED = 0.2
    ADD_INTERVAL = 4000

    def __init__(self, heart_img, y):
        super(Heart, self).__init__()
        self.image = heart_img
        self.x = WIN_WIDTH
        self.y = y
        self.mask = pygame.mask.from_surface(self.image)

    @property
    def rect(self):
        return Rect(self.x, self.y, self.image.get_width(), self.image.get_height())

    def update(self, delta_frames=1):
        self.x -= Heart.SPEED * frames_to_msec(delta_frames)


def load_images():
    def load_image(img_file_name):
        file_name = os.path.join(os.path.dirname(__file__), 'images', img_file_name)
        img = pygame.image.load(file_name)
        img.convert_alpha()
        return img

    return {'background': load_image('background.png'),
            'pipe-end': load_image('pipe_end.png'),
            'pipe-body': load_image('pipe_body.png'),
            'bird-wingup': load_image('bird_wing_up.png'),
            'bird-wingdown': load_image('bird_wing_down.png'),
            'rocket': load_image('rocket.png'),
            'heart': load_image('heart.png')}


def frames_to_msec(frames, fps=FPS):
    return 1000.0 * frames / fps


def msec_to_frames(milliseconds, fps=FPS):
    return fps * milliseconds / 1000.0


def draw_energy_bar(surface, bird):
    bar_x, bar_y = 10, 10
    bar_width, bar_height = 100, 15
    energy_ratio = bird.energy
    fill_width = int(bar_width * energy_ratio)

    pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
    color = (0, 200, 0) if energy_ratio > 0.3 else (200, 50, 50)
    pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))
    pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)


def main():
    pygame.init()
    display_surface = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption('Flappy Bird with Energy + Hearts')

    clock = pygame.time.Clock()
    score_font = pygame.font.SysFont(None, 32, bold=True)
    images = load_images()

    bird = Bird(50, int(WIN_HEIGHT/2 - Bird.HEIGHT/2), 2,
                (images['bird-wingup'], images['bird-wingdown']))

    pipes = deque()
    rockets = deque()
    hearts = deque()

    frame_clock = 0
    score = 0
    done = paused = False
    while not done:
        clock.tick(FPS)
        display_surface.fill((0, 0, 0))
        display_surface.blit(images['background'], (0, 0))

        if not (paused or frame_clock % msec_to_frames(PipePair.ADD_INTERVAL)):
            pipes.append(PipePair(images['pipe-end'], images['pipe-body']))

        if not (paused or frame_clock % msec_to_frames(Rocket.ADD_INTERVAL)):
            rockets.append(Rocket(images['rocket'], randint(50, WIN_HEIGHT - 50), bird.x))

        if not (paused or frame_clock % msec_to_frames(Heart.ADD_INTERVAL)):
            hearts.append(Heart(images['heart'], randint(50, WIN_HEIGHT - 50)))

        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = True
                break
            elif e.type == KEYUP and e.key in (K_PAUSE, K_p):
                paused = not paused
            elif e.type == MOUSEBUTTONUP or (e.type == KEYUP and
                    e.key in (K_UP, K_RETURN, K_SPACE)):
                bird.flap()

        if paused:
            continue

        if any(p.collides_with(bird) for p in pipes) or bird.y < 0 or bird.y > WIN_HEIGHT - Bird.HEIGHT:
            done = True

        while pipes and not pipes[0].visible:
            pipes.popleft()

        for p in pipes:
            p.update()
            display_surface.blit(p.image, p.rect)

        for r in list(rockets):
            r.update()
            display_surface.blit(r.image, r.rect)
            if r.check_trigger(bird):
                done = True
            if r.x + r.image.get_width() < 0:
                rockets.popleft()

        for h in list(hearts):
            h.update()
            display_surface.blit(h.image, h.rect)
            if h.rect.colliderect(bird.rect):
                score += 5
                bird.regen_energy(1/5)
                hearts.remove(h)
            elif h.x + h.image.get_width() < 0:
                hearts.popleft()

        bird.update()
        display_surface.blit(bird.image, bird.rect)

        for p in pipes:
            if p.x + PipePair.WIDTH < bird.x and not p.score_counted:
                score += 1
                p.score_counted = True

        score_surface = score_font.render(str(score), True, (255, 255, 255))
        score_x = WIN_WIDTH/2 - score_surface.get_width()/2
        display_surface.blit(score_surface, (score_x, PipePair.PIECE_HEIGHT))

        draw_energy_bar(display_surface, bird)

        pygame.display.flip()
        frame_clock += 1

    print('Game over! Score: %i' % score)
    pygame.quit()


if __name__ == '__main__':
    main()
