#!/usr/bin/env python3
"""
Elden Ring — Mini Prototype (single-file)
Top-down action: movement, roll/dodge, light/heavy attacks, stamina, simple enemies.
Controls:
 - WASD / Arrow keys: Move
 - J or Left mouse: Light attack
 - K: Heavy attack
 - Space: Roll / Dodge
 - Esc: Quit
Note: small educational prototype inspired by Souls-like mechanics.
"""
import math, random, time
import pygame
from pygame import Rect, Vector2

WIDTH, HEIGHT = 1920, 1080
FPS = 120


PLAYER_SPEED = 180
ROLL_SPEED = 420
ATTACK_RANGE = 48
ATTACK_COOLDOWN = 0.45
ROLL_COOLDOWN = 0.8
INVULN_TIME = 0.28
STAMINA_MAX = 100
STAMINA_RECOVERY_RATE = 20  # per second
LIGHT_ATTACK_COST = 12
HEAVY_ATTACK_COST = 28
HEAVY_ATTACK_COOLDOWN = 1.0

ENEMY_SPEED = 100
ENEMY_DAMAGE = 12

# Init
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)

def clamp(x, a, b): return max(a, min(b, x))

def draw_bar(surf, rect, pct, bg=(40,40,40), fg=(100,200,100)):
    pygame.draw.rect(surf, bg, rect)
    inner = Rect(rect.x+2, rect.y+2, max(0, int((rect.w-4)*pct)), rect.h-4)
    pygame.draw.rect(surf, fg, inner)
    pygame.draw.rect(surf, (0,0,0), rect, 2)

class Entity:
    def __init__(self, pos, radius=18):
        self.pos = Vector2(pos)
        self.vel = Vector2(0,0)
        self.radius = radius
        self.hp = 100
        self.max_hp = 100
        self.alive = True
        self.invuln_timer = 0.0
    def update_timers(self, dt):
        if self.invuln_timer>0:
            self.invuln_timer = max(0, self.invuln_timer - dt)
    def take_damage(self, amount, source=None):
        if self.invuln_timer>0 or not self.alive: return False
        self.hp -= amount
        self.invuln_timer = 0.5
        if self.hp<=0:
            self.alive = False
        return True
    def draw_health(self, surf, offset=(0,-30)):
        pct = clamp(self.hp/self.max_hp if self.max_hp>0 else 0, 0, 1)
        rect = Rect(int(self.pos.x-30+offset[0]), int(self.pos.y+offset[1]), 60, 8)
        draw_bar(surf, rect, pct, bg=(70,20,20), fg=(200,60,60))

class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos, radius=16)
        self.max_hp = 120
        self.hp = self.max_hp
        self.stamina = STAMINA_MAX
        self.attack_timer = 0.0
        self.attack_cooldown = 0.0
        self.roll_timer = 0.0
        self.roll_cooldown = 0.0
        self.facing = Vector2(1,0)
        self.is_rolling = False
        self.invuln_timer = 0.0

    def update(self, dt, keys, mouse_pos, mouse_buttons):
        self.update_timers(dt)
        mv = Vector2(0,0)
        if keys[pygame.K_w] or keys[pygame.K_UP]: mv.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: mv.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: mv.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: mv.x += 1
        if mv.length_squared()>0:
            mv = mv.normalize()
            self.facing = mv

        if not self.is_rolling:
            self.stamina = clamp(self.stamina + STAMINA_RECOVERY_RATE * dt, 0, STAMINA_MAX)

        if self.roll_cooldown<=0 and (keys[pygame.K_SPACE] or mouse_buttons[2]):
            if self.stamina >= 20:
                self.is_rolling = True
                self.roll_timer = 0.26
                self.roll_cooldown = ROLL_COOLDOWN
                self.invuln_timer = INVULN_TIME
                self.stamina -= 20
                self.vel = self.facing * ROLL_SPEED

        attacking = False
        if self.attack_cooldown<=0 and (keys[pygame.K_j] or mouse_buttons[0]):
            if self.stamina >= LIGHT_ATTACK_COST:
                self.attack_timer = 0.18
                self.attack_cooldown = ATTACK_COOLDOWN
                self.stamina -= LIGHT_ATTACK_COST
                attacking = True
        if self.attack_cooldown<=0 and (keys[pygame.K_k]):
            if self.stamina >= HEAVY_ATTACK_COST:
                self.attack_timer = 0.34
                self.attack_cooldown = HEAVY_ATTACK_COOLDOWN
                self.stamina -= HEAVY_ATTACK_COST
                attacking = True

        if self.attack_timer>0:
            self.attack_timer = max(0, self.attack_timer - dt)
        if self.attack_cooldown>0:
            self.attack_cooldown = max(0, self.attack_cooldown - dt)
        if self.roll_timer>0:
            self.roll_timer = max(0, self.roll_timer - dt)
            if self.roll_timer==0:
                self.is_rolling = False
                self.vel = Vector2(0,0)
        if self.roll_cooldown>0:
            self.roll_cooldown = max(0, self.roll_cooldown - dt)

        if not self.is_rolling and not attacking:
            target_vel = mv * PLAYER_SPEED
            self.vel += (target_vel - self.vel) * clamp(10*dt, 0, 1)
        self.pos += self.vel * dt
        self.pos.x = clamp(self.pos.x, 20, WIDTH-20)
        self.pos.y = clamp(self.pos.y, 20, HEIGHT-20)

    def draw(self, surf):
        if self.invuln_timer>0:
            pygame.draw.circle(surf, (200,200,60), (int(self.pos.x), int(self.pos.y)), int(self.radius+8), 2)
        pygame.draw.circle(surf, (50,120,200), (int(self.pos.x), int(self.pos.y)), self.radius)
        tip = self.pos + self.facing.normalize()* (self.radius+8)
        pygame.draw.line(surf, (220,220,220), self.pos, tip, 3)
        self.draw_health(surf)

    def attack_hitbox(self):
        if self.attack_timer>0:
            length = ATTACK_RANGE
            center = self.pos + self.facing.normalize()* (self.radius + length/2)
            radius = length/1.6
            return (center, radius)
        return None

class Enemy(Entity):
    def __init__(self, pos):
        super().__init__(pos, radius=16)
        self.max_hp = 80
        self.hp = self.max_hp
        self.attack_cooldown = 0.0
        self.speed = ENEMY_SPEED
        self.respawn_time = 0

    def update(self, dt, player: Player):
        self.update_timers(dt)
        if not self.alive:
            if self.respawn_time<=0:
                self.respawn_time = random.uniform(3.0, 6.0)
            else:
                self.respawn_time -= dt
                if self.respawn_time<=0:
                    self.alive = True
                    self.hp = self.max_hp
            return

        to_player = player.pos - self.pos
        dist = to_player.length()
        if dist < 300:
            if dist> (self.radius+player.radius+6):
                self.vel = to_player.normalize()*self.speed
                self.pos += self.vel * dt
            else:
                if self.attack_cooldown<=0 and player.invuln_timer<=0:
                    self.attack_cooldown = 1.0
                    player.take_damage(ENEMY_DAMAGE)
            if self.attack_cooldown>0:
                self.attack_cooldown = max(0, self.attack_cooldown - dt)
        else:
            self.vel *= 0.9
            if random.random()<0.01:
                ang = random.random()*math.tau
                self.vel = Vector2(math.cos(ang), math.sin(ang))* (self.speed*0.5)
            self.pos += self.vel*dt
        self.pos.x = clamp(self.pos.x, 20, WIDTH-20)
        self.pos.y = clamp(self.pos.y, 20, HEIGHT-20)

    def draw(self, surf):
        if not self.alive:
            pygame.draw.circle(surf, (80,80,80), (int(self.pos.x), int(self.pos.y)), self.radius)
            return
        pygame.draw.circle(surf, (180,80,70), (int(self.pos.x), int(self.pos.y)), self.radius)
        self.draw_health(surf)

def circle_collide(a_pos, a_r, b_pos, b_r):
    return (a_pos - b_pos).length_squared() <= (a_r + b_r)**2

player = Player(Vector2(WIDTH/2, HEIGHT/2))
enemies = [Enemy(Vector2(random.randint(100, WIDTH-100), random.randint(100, HEIGHT-100))) for _ in range(4)]

def draw_hud(surf, player):
    draw_bar(surf, Rect(12,12,220,22), clamp(player.hp/player.max_hp, 0, 1), bg=(50,10,10), fg=(220,80,60))
    hp_text = font.render(f"HP: {int(player.hp)}/{player.max_hp}", True, (255,255,255))
    surf.blit(hp_text, (14,14))
    draw_bar(surf, Rect(12,42,220,14), clamp(player.stamina/STAMINA_MAX, 0, 1), bg=(30,30,30), fg=(160,200,120))
    st_text = font.render(f"STA: {int(player.stamina)}", True, (255,255,255))
    surf.blit(st_text, (14,42))
    y = 68
    surf.blit(font.render(f"Atk CD: {player.attack_cooldown:.2f}s", True, (220,220,220)), (14,y))
    surf.blit(font.render(f"Roll CD: {player.roll_cooldown:.2f}s", True, (220,220,220)), (120,y))

def main_loop():
    running = True
    while running:
        dt = clock.tick(FPS)/1000.0
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                running = False
            if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = Vector2(pygame.mouse.get_pos())

        player.update(dt, keys, mouse_pos, mouse_buttons)
        for e in enemies:
            e.update(dt, player)

        hit = player.attack_hitbox()
        if hit:
            center, radius = hit
            for en in enemies:
                if en.alive and circle_collide(center, radius, en.pos, en.radius):
                    en.take_damage(28)
                    dir = (en.pos - player.pos)
                    if dir.length_squared()>0:
                        en.pos += dir.normalize()*12

        screen.fill((18,18,30))
        for gx in range(0, WIDTH, 64):
            pygame.draw.line(screen, (12,12,20), (gx,0),(gx,HEIGHT))
        for gy in range(0, HEIGHT, 64):
            pygame.draw.line(screen, (12,12,20), (0,gy),(WIDTH,gy))

        for en in enemies:
            en.draw(screen)
        player.draw(screen)

        if hit:
            c, r = hit
            pygame.draw.circle(screen, (240,220,120), (int(c.x), int(c.y)), int(r), 2)

        draw_hud(screen, player)

        alive_n = sum(1 for e in enemies if e.alive)
        screen.blit(font.render(f"Enemies alive: {alive_n}", True, (240,240,240)), (WIDTH-160, 12))

        if alive_n==0 and random.random()<0.01:
            enemies.clear()
            for _ in range(4):
                enemies.append(Enemy(Vector2(random.randint(60, WIDTH-60), random.randint(60, HEIGHT-60))))

        pygame.display.flip()

    pygame.quit()

if __name__=='__main__':
    print("Elden Ring Mini Prototype\nControls: WASD, J/K, Space, Mouse. Close window or press Esc to quit.")
    main_loop()