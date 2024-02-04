from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import objects.objects as objects
from objects.menu import buyMenu, turretMenu, settingsMenu, animations
from random import choice, randint, uniform
import json
import math
import pygame

pygame.init()
pygame.mixer.quit()
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()

pygame.display.set_icon(pygame.image.load("sprites/other/icon.gif"))
pygame.display.set_caption("Tower Defence")

text_font_2xl = pygame.font.Font('media/other/Adobe Dia.ttf', 400)
text_font_xl = pygame.font.Font('media/other/Adobe Dia.ttf', 200)
text_font_l = pygame.font.Font('media/other/Adobe Dia.ttf', 90)
text_font_m = pygame.font.Font('media/other/Adobe Dia.ttf', 70)
text_font_s = pygame.font.Font('media/other/Adobe Dia.ttf', 50)


class Game:
    def __init__(self):
        self.res = (1000, 700)
        self.clock = pygame.time.Clock()
        self.Screen = pygame.display.set_mode(self.res)
        self.selected_tile = self.set_selected_tile()

        with open("data/levels.json") as f:
            self.levels = json.load(f)
        with open("data/waves.json") as f:
            self.waves = json.load(f)
        with open("data/settings.json") as f:
            settings = json.load(f)
            self.music_volume = settings['music_volume']
            self.sfx_volume = settings['sfx_volume']
            self.parallax_mod = settings['parallax_mod']

        self.indicator = pygame.image.load('sprites/other/indicator.png').convert_alpha()

        self.tiles = []
        self.enemies = []
        self.turrets = []
        self.support = []
        self.bg_beams = []
        self.turret_pos = []
        self.killed_enemies = []
        self.parallax_move = [0, 0]
        self.active_animations = []
        self.buy_menu_pos = [-50, -100]
        self.l_arr_color = [200, 200, 200]
        self.r_arr_color = [200, 200, 200]
        self.turret_menu_pos = [-50, -100]
        self.hue = choice([[255, 0, 0], [0, 255, 0], [0, 0, 255]])
        self.available_turrets = [eval(f"objects.Kinetic_{x}([-1000, -1000], False)") for x in range(1, 4)] + [
            eval(f"objects.Support_{x}([-1000, -1000], False)") for x in range(1, 4)]
        self.tile_sprites = [pygame.image.load(f'sprites/path/tile_{x}.png').convert() for x in range(1, 5)]
        self.backgrounds = [[
            pygame.image.load("sprites/other/background.png").convert(),
            [self.res[0] * x, -50]] for x in range(-1, 2)]
        self.turret_menu_buttons = [[x, [-50, -100],
                                     pygame.transform.scale(pygame.image.load(f"sprites/buttons/turretMenu/{x}.png"),
                                                            (40, 40))] for x in ['sell', 'upgrade']]

        self.sfx = {
            "menu_nav": pygame.mixer.Sound("media/sfx/menu/menu_nav.wav"),
            "game_over": pygame.mixer.Sound("media/sfx/menu/game_over.wav")
        }

        for index in range(0, 3):
            self.sfx[f"shoot_{index}"] = pygame.mixer.Sound(f"media/sfx/shoot/shoot_{index + 1}.wav")

        for index in range(0, 4):
            for i in range(1, 3):
                self.sfx[f"explode_{index}_{i}"] = pygame.mixer.Sound(f"media/sfx/explode/explode_{index + 1}_{i}.wav")

        for index in range(0, 3):
            self.sfx[f"shop_{index}"] = pygame.mixer.Sound(f"media/sfx/menu/buy_{index + 1}.wav")

        self.FPS = 120
        self.NOTIF_Y = 100
        self.COST_Y = 50
        self.INFO_Y = self.res[1] // 1.1
        self.VOLUME_MOD = 0.1

        self.turret_menu_width = len(self.turret_menu_buttons)
        self.buy_menu_width = len(self.available_turrets)
        self.enemy_send_timer = 300
        self.bg_beam_cooldown = 15
        self.enemy_send_index = 0
        self.enemy_type_index = 0
        self.intro_frame_count = 0
        self.selected_level = 1
        self.intro_timer = 30
        self.health = 50
        self.money = 500
        self.level = -1
        self.wave = 0
        self.kills = 0
        self.wave_text_width = len(f"Wave {self.wave}")
        self.level_length = len(self.levels[self.selected_level])

        self.turret_string = " "
        self.selected_tr = " "

        self.turret_menu_open = False
        self.buy_menu_open = False
        self.intro_playing = True
        self.intro_menu_t_played = False
        self.game_run = True
        self.run = True
        self.pause = False

        self.title_text = text_font_xl.render("Tower Defence", True, (250, 250, 250))
        self.cost_text = text_font_l.render(" ", True, (255, 255, 255))
        self.notif_text = text_font_s.render(" ", True, (255, 100, 100))
        self.tower_info_text = text_font_m.render(" ", True, (230, 230, 230))
        self.money_text = text_font_m.render(str(self.money) + " $", True, (150, 255, 150))
        self.health_text = text_font_m.render(str(self.health), True, (255, 150, 150))
        self.last_credits_text = text_font_m.render("PLease Pavel Mesenev", True, (150, 255, 150))
        self.last_1_credits_text = text_font_m.render("100/100 points", True, (150, 255, 150))
        self.level_menu_index = text_font_xl.render(f"Level {self.selected_level}", True, [255, 255, 255])
        self.dev_credits_text = text_font_m.render("Thanks for playing ;)", True, (150, 255, 150))
        self.game_over_text_1 = text_font_xl.render("Game Over", True, (255, 255, 255))
        self.game_over_text_2 = text_font_l.render("Good luck next time!", True, (155, 155, 155))
        self.game_over_stats = text_font_m.render(f"Kills: {self.kills}", True, (200, 200, 200))
        self.wave_text = text_font_m.render(f"Wave {self.wave + 1}", True, (255, 255, 255))
        self.pause_title = text_font_xl.render("Game Paused", True, (250, 250, 250))

        self.title_text_center = self.title_text.get_rect(center=(self.res[0] // 2, self.res[1] // 5))
        self.cost_center = self.cost_text.get_rect(
            center=(self.res[0] // 2 + self.parallax_move[0], self.COST_Y + self.parallax_move[1])
        )
        self.level_menu_index_center = self.level_menu_index.get_rect(
            center=(self.res[0] // 2, self.res[1] // 2 - 50)
        )
        self.notif_text_center = self.notif_text.get_rect(
            center=(self.res[0] // 2 + self.parallax_move[0], self.NOTIF_Y + self.parallax_move[1])
        )
        self.tower_info_text_center = self.tower_info_text.get_rect(
            center=(self.res[0] // 2 + self.parallax_move[0] / 7 + 25, self.INFO_Y + self.parallax_move[1] / 7)
        )
        self.music_credits_text_center = self.last_credits_text.get_rect(
            center=(self.res[0] / 2, self.res[1] / 2 + 100))
        self.art_credits_text_center = self.last_1_credits_text.get_rect(center=(self.res[0] / 2, self.res[1] / 2))
        self.dev_credits_text_center = self.dev_credits_text.get_rect(center=(self.res[0] / 2, self.res[1] / 2 - 100))
        self.game_over_text_1_center = self.game_over_text_1.get_rect(center=(self.res[0] // 2, self.res[1] // 4 - 5))
        self.game_over_text_2_center = self.game_over_text_2.get_rect(center=(self.res[0] // 2, self.res[1] // 4 + 75))
        self.game_over_stats_center = self.game_over_stats.get_rect(center=(self.res[0] // 2, self.res[1] // 2))
        self.pause_title_center = self.pause_title.get_rect(center=(self.res[0] // 2, self.res[1] // 5))

        self.new_game_button = objects.newGameButton((self.res[0] // 3.5 - 175, 255, 350, 80))
        self.settings_button = objects.settingsButton((self.res[0] // 3.5 - 175, 385, 350, 80))
        self.credits_button = objects.creditsButton((self.res[0] // 3.5 - 175, 515, 350, 80))
        self.main_menu_buttons = [self.new_game_button, self.settings_button, self.credits_button]

        self.audio_settings_button = objects.audioSettingsButton(
            (self.res[0] / 2 - 260, self.res[1] // 2 - 120, 520, 100))
        self.video_settings_button = objects.videoSettingsButton(
            (self.res[0] / 2 - 260, self.res[1] // 2 + 35, 520, 100))
        self.back_button = objects.backButton((self.res[0] // 2 - 75, self.res[1] // 1.275, 150, 80))
        self.settings_buttons = [self.audio_settings_button, self.video_settings_button, self.back_button]

        self.resume_button = objects.resumeButton((self.res[0] // 2 - 175, self.res[1] // 2 - 110, 350, 80))
        self.settings_pause_button = objects.settingsButton((self.res[0] // 2 - 175, self.res[1] // 2, 350, 80))
        self.back_to_menu_button = objects.menuButton((self.res[0] // 2 - 175, self.res[1] // 2 + 110, 350, 80))
        self.pause_menu_buttons = [self.resume_button, self.settings_pause_button, self.back_to_menu_button]

        self.play_level_button = objects.playLevelButton((self.res[0] // 2 - 150, self.res[1] // 2 + 50, 300, 80))
        self.level_menu_buttons = [self.back_button, self.play_level_button]

        self.try_again_button = objects.tryAgainButton((self.res[0] // 2 - 260, self.res[1] // 2 + 75, 520, 100))

        for key in self.sfx:
            self.sfx[key].set_volume(self.sfx_volume * self.VOLUME_MOD)

    def play_intro(self):
        while self.intro_playing:
            self.clock.tick(self.FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                    self.intro_playing = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.intro_playing = False

            pygame.display.update()

        if self.run:
            self.main_menu()

    def main_menu(self):
        self.load_music("main_menu.mp3", self.music_volume)
        self.load_level()
        self.enemy_send_timer = 60

        while self.run:
            self.clock.tick(self.FPS)
            pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

                if event.type == pygame.MOUSEMOTION:

                    self.set_parallax()
                    for button in self.main_menu_buttons:
                        if button.isOver(pos):
                            button.color = button.clicked_color
                        else:
                            button.color = button.default_color

                if event.type == pygame.MOUSEBUTTONDOWN:

                    self.active_animations.append(animations.CircleAnimation(
                        [randint(60, 100), randint(60, 100), randint(60, 100)],
                        pos, 1, 1, substract=2)
                    )
                    if self.main_menu_buttons[0].isOver(pos):  # new game
                        self.sfx['menu_nav'].play()
                        self.level_menu()

                    elif self.main_menu_buttons[1].isOver(pos):  # settings
                        self.main_menu_buttons[1].color = self.main_menu_buttons[1].default_color
                        self.sfx['menu_nav'].play()
                        settingsMenu.settings_active(self)

                    elif self.main_menu_buttons[2].isOver(pos):  # credits
                        self.main_menu_buttons[2].color = self.main_menu_buttons[2].default_color
                        self.sfx['menu_nav'].play()
                        self.show_credits()

            if self.enemy_send_timer > 0:
                self.enemy_send_timer -= 1
            else:
                choices = ["Circle_1", "Circle_2", "Square_1", "Square_2"]
                self.enemies.append(eval(f'objects.{choice(choices)}(self.levels[self.level][0])'))
                self.enemy_send_timer = 60
                self.health = 50
# Я очень старался, надеюсь вам понравится код и и приложение)
            for en in self.enemies:
                self.move_enemy(en)

            if self.run:
                self.draw_menu()

    def level_menu(self):

        show_level_menu = True
        while show_level_menu and self.run:
            self.clock.tick(self.FPS)
            pos = pygame.mouse.get_pos()
            index_update = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

                if event.type == pygame.MOUSEMOTION:
                    for button in self.level_menu_buttons:
                        if button.isOver(pos):
                            button.color = button.clicked_color
                        else:
                            button.color = button.default_color

                    if pos[0] < 150:
                        self.l_arr_color = [125, 125, 125]
                    else:
                        self.l_arr_color = [200, 200, 200]

                    if pos[0] > self.res[0] - 150:
                        self.r_arr_color = [125, 125, 125]
                    else:
                        self.r_arr_color = [200, 200, 200]

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.level_menu_buttons[0].isOver(pos):
                        self.sfx['menu_nav'].play()
                        show_level_menu = False

                    elif self.level_menu_buttons[1].isOver(pos):
                        self.sfx['menu_nav'].play()
                        self.level = self.selected_level - 1
                        show_level_menu = False
                        self.level_run()

                    elif pos[0] < 150:
                        self.sfx['menu_nav'].play()
                        if self.selected_level > 1:
                            self.selected_level -= 1
                        else:
                            self.selected_level = len(self.levels) - 1
                        index_update = True

                    elif pos[0] > self.res[0] - 150:
                        self.sfx['menu_nav'].play()
                        if self.selected_level < len(self.levels) - 1:
                            self.selected_level += 1
                        else:
                            self.selected_level = 1
                        index_update = True

                    if index_update:
                        self.level_menu_index = text_font_xl.render(
                            f"Level {self.selected_level}",
                            True, [255, 255, 255]
                        )
                        self.level_menu_index_center = self.level_menu_index.get_rect(
                            center=(self.res[0] // 2, self.res[1] // 2 - 50)
                        )

            self.draw_level_menu()
#ds
    def game_over(self):

        self.main_menu_buttons[0].color = self.main_menu_buttons[0].default_color
        self.game_over_stats = text_font_m.render(
            f"Kills: {self.kills}",
            True,
            (200, 200, 200)
        )
        pygame.mixer.music.stop()
        self.sfx['game_over'].play()
        self.level = -1
        show_game_over = True
        while show_game_over and self.run:
            self.clock.tick(self.FPS)
            pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

                if event.type == pygame.MOUSEMOTION:

                    self.set_parallax()
                    if self.try_again_button.isOver(pos):
                        self.try_again_button.color = self.try_again_button.clicked_color
                    else:
                        self.try_again_button.color = self.try_again_button.default_color

                if event.type == pygame.MOUSEBUTTONDOWN:

                    self.active_animations.append(animations.CircleAnimation(
                        [randint(60, 100), randint(60, 100), randint(60, 100)],
                        pos,
                        1,
                        1,
                        substract=2)
                    )
                    if self.try_again_button.isOver(pos):
                        self.sfx['menu_nav'].play()
                        show_game_over = False

            self.draw_game_over()

        self.load_music("main_menu.mp3", self.music_volume)
        self.load_level()

    def show_credits(self):
        show_credits = True
        while show_credits:
            self.clock.tick(self.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    show_credits = False

                if event.type == pygame.MOUSEMOTION:
                    self.set_parallax()

            self.draw_credits()

    def level_run(self):
        self.load_music("level.mp3", self.music_volume)
        self.load_level()
        self.kills = 0
        self.game_run = True

        while self.run and self.game_run:
            self.clock.tick(self.FPS)
            pos = pygame.mouse.get_pos()
            keys = pygame.key.get_pressed()
            self.selected_tile = self.set_selected_tile()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

                if event.type == pygame.MOUSEMOTION:

                    self.set_parallax()
                    if self.buy_menu_open:
                        buyMenu.hover(self)
                    elif self.turret_menu_open:
                        turretMenu.hover(self)

                if event.type == pygame.MOUSEBUTTONDOWN:

                    self.active_animations.append(animations.CircleAnimation(
                        [randint(60, 100), randint(60, 100), randint(60, 100)],
                        pos,
                        1,
                        1,
                        substract=2)
                    )

                    if self.buy_menu_open:
                        if buyMenu.operate(self):
                            new_tr = eval(self.turret_string)
                            if new_tr.type == 'support':
                                self.support.append(new_tr)
                                self.apply_support(self.support[-1])
                            else:
                                for sp in self.support:
                                    self.apply_support(sp, True)
                                self.turrets.append(new_tr)
                                for sp in self.support:
                                    self.apply_support(sp)

                    elif self.turret_menu_open:
                        turretMenu.operate(self)
                    elif self.selected_tile in self.turret_pos:
                        turretMenu.activate(self)
                    elif self.selected_tile in self.tiles:
                        buyMenu.activate(self)

            if keys[pygame.K_ESCAPE]:
                self.sfx['menu_nav'].play()
                self.pause_menu()

            if self.enemy_send_timer > 0:
                self.enemy_send_timer -= 1
            else:
                to_send = self.waves[self.wave][self.enemy_type_index][0]
                self.enemies.append(eval(f"objects.{to_send}(self.levels[self.level][0])"))
                self.enemy_send_index += 1
                self.enemy_send_timer = self.waves[self.wave][self.enemy_type_index][2]

                if self.enemy_send_index == 1 and self.enemy_type_index == 0:  # editing 'wave' text
                    self.wave_text = text_font_m.render(
                        f"Wave {self.wave + 1}",
                        True,
                        (255, 255, 255)
                    )
                    self.wave_text_width = len(f"Wave {self.wave + 1}")
                    animation_center = list(map(
                        round,
                        (self.res[0] - 30 - 13 * self.wave_text_width + self.parallax_move[0] / 5,
                         55 + self.parallax_move[1] / 5
                         )
                    ))
                    self.active_animations.append(animations.CircleAnimation(
                        [200, 200, 200],
                        animation_center
                    ))

                if self.enemy_send_index >= self.waves[self.wave][self.enemy_type_index][1]:
                    if len(self.waves[self.wave]) - 1 <= self.enemy_type_index:
                        if self.wave != len(self.waves) - 1:  # new wave
                            self.wave += 1
                            self.enemy_send_timer = 300
                            self.enemy_send_index = 0
                            self.enemy_type_index = 0
                        else:
                            print('Game Finished - No more waves left')

                    else:
                        self.enemy_send_index = 0
                        self.enemy_type_index += 1

            for en in self.enemies:
                self.move_enemy(en)

            if self.run and self.game_run:
                self.detect_enemy()
                self.draw_game()

        self.game_over()

    def pause_menu(self):
        self.pause = True
        pygame.mixer.music.pause()
        while self.pause and self.run:
            self.clock.tick(self.FPS)
            pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

                if event.type == pygame.MOUSEMOTION:
                    self.set_parallax()

                    for button in self.pause_menu_buttons:
                        if button.isOver(pos):
                            button.color = button.clicked_color
                        else:
                            button.color = button.default_color

                if event.type == pygame.MOUSEBUTTONDOWN:

                    if self.pause_menu_buttons[0].isOver(pos):
                        self.pause = False
                        self.sfx['menu_nav'].play()
                        pygame.mixer.music.unpause()

                    elif self.pause_menu_buttons[1].isOver(pos):
                        self.pause_menu_buttons[1].color = self.pause_menu_buttons[1].default_color
                        self.sfx['menu_nav'].play()
                        settingsMenu.settings_active(self)

                    elif self.pause_menu_buttons[2].isOver(pos):
                        self.pause_menu_buttons[2].color = self.pause_menu_buttons[2].default_color
                        self.sfx['menu_nav'].play()
                        self.pause = False
                        self.game_run = False
                        self.level = -1
                        self.load_level()

            self.draw_pause()

    def apply_support(self, sp, substract=False):
        neg = 1
        if substract:
            neg = -1

        for tr in self.turrets:
            distance = math.hypot(tr.x - sp.x, tr.y - sp.y)
            if distance > sp.range_:
                continue

            tr.dmg += sp.effects['dmg'] * neg
            tr.range_ += sp.effects['range'] * neg
            tr.shoot_cooldown_d += sp.effects['shoot_cooldown_d'] * neg
            print('test')

    def set_parallax(self):

        pos = pygame.mouse.get_pos()
        if self.parallax_mod > 0.02:
            self.parallax_move = [
                ((self.res[0] // 2 - pos[0]) / 20) * self.parallax_mod,
                ((self.res[1] // 2 - pos[1]) / 15) * self.parallax_mod
            ]

    @staticmethod
    def set_selected_tile():
        pos = list(pygame.mouse.get_pos())

        return list((math.floor(pos[0] / 50) * 50, math.floor(pos[1] / 50) * 50))

    def load_music(self, name, volume=0.1, looped=True, path="media/music/"):
        pygame.mixer.music.load(f"{path}{name}")
        pygame.mixer.music.set_volume(volume * self.VOLUME_MOD)

        if looped:
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.play()

    def load_level(self):
        self.health = 50
        self.money = 500
        self.wave = 0
        self.enemy_send_timer = 300
        self.enemy_send_index = 0
        self.enemy_type_index = 0
        self.level += 1
        self.tiles = []
        self.enemies = []
        self.turrets = []
        self.support = []
        self.turret_pos = []
        self.killed_enemies = []
        self.wave_text = text_font_m.render(
            f"Wave {self.wave + 1}",
            True,
            (255, 255, 255)
        )
        self.wave_text_width = len(f"Wave {self.wave}")
        self.money_text = text_font_m.render(
            str(self.money) + " $",
            True,
            (255, 255, 255)
        )
        self.health_text = text_font_m.render(
            str(self.health),
            True,
            (255, 150, 150)
        )

        self.level_length = len(self.levels[self.level])
        for square in self.levels[self.level]:
            for offset in [[0, 50], [50, 50], [50, 0], [50, -50], [0, -50], [-50, -50], [-50, 0], [-50, 50]]:
                if not [square[0] + offset[0], square[1] + offset[1]] in self.levels[self.level]:
                    self.tiles.append([square[0] + offset[0], square[1] + offset[1]])

    def detect_enemy(self):
        for tr in self.turrets:
            if tr.shoot_cooldown > 0:
                tr.shoot_cooldown -= 1
            for en in self.enemies:
                if tr.attack_target(en):
                    self.sfx[f"shoot_{tr.id}"].play()
                    break
                if en.health <= 0:
                    self.sfx[f"explode_{en.id}_{randint(1, 2)}"].play()
                    self.money += en.value
                    self.money_text = text_font_m.render(
                        str(self.money) + " $",
                        True,
                        (255, 255, 255)
                    )
                    self.killed_enemies.append(en)
                    self.enemies.remove(en)
                    self.kills += 1
                    self.set_parallax()

    def move_enemy(self, en):
        x_value = en.x - 25 + en.x_offset
        y_value = en.y - 25 + en.y_offset

        if x_value > self.levels[self.level][en.point][0]:
            en.x -= en.v
        elif x_value < self.levels[self.level][en.point][0]:
            en.x += en.v
        elif y_value > self.levels[self.level][en.point][1]:
            en.y -= en.v
        elif y_value < self.levels[self.level][en.point][1]:
            en.y += en.v

        else:
            if en.point + 1 < self.level_length:
                en.point += 1
            else:
                self.health -= en.dmg
                self.enemies.remove(en)
                self.health_text = text_font_m.render(
                    str(self.health),
                    True,
                    (255, 150, 150)
                )
                if self.health <= 0:
                    self.game_run = False

    def draw_board(self):

        for en in self.killed_enemies:  # explosions
            en.explode_2(self.Screen)
            if en.exploded_2_radius > self.res[0]:
                self.killed_enemies.remove(en)

        for p in self.levels[self.level]:
            if self.levels[self.level].index(p) == 0:
                self.Screen.blit(self.tile_sprites[3], (p[0], p[1], 50, 50))
            elif self.levels[self.level].index(p) == len(self.levels[self.level]) - 1:
                self.Screen.blit(self.tile_sprites[2], (p[0], p[1], 50, 50))
            else:
                self.Screen.blit(self.tile_sprites[1], (p[0], p[1], 50, 50))

        for t in self.tiles:
            self.Screen.blit(self.tile_sprites[0], (t[0], t[1], 50, 50))

        for en in self.enemies:
            en.draw(self.Screen)
        for tr in self.turrets + self.support:
            tr.draw(self.Screen)

        for en in self.killed_enemies:  # explosions
            en.explode_1(self.Screen)

    def draw_bg(self):

        self.Screen.fill((20, 20, 30))
        beam_render = False

        if self.bg_beam_cooldown > 0 and self.bg_beam_cooldown not in [5, 10, 15]:
            self.bg_beam_cooldown -= 1
            x_v = 0
            y_v = 0
        elif self.bg_beam_cooldown == 15:
            self.bg_beam_cooldown -= 1
            v = uniform(0, 1)
            x_v = v
            y_v = 1 - v
            beam_render = True

        elif self.bg_beam_cooldown == 10:
            self.bg_beam_cooldown -= 1
            v = uniform(0, 1)
            x_v = -v
            y_v = 1 - v
            beam_render = True

        elif self.bg_beam_cooldown == 5:
            self.bg_beam_cooldown -= 1
            v = uniform(0, 1)
            x_v = -v
            y_v = v - 1
            beam_render = True

        else:
            self.bg_beam_cooldown = 20
            v = uniform(0, 1)
            x_v = v
            y_v = v - 1
            beam_render = True

        if beam_render:
            color = randint(20, 50)
            m = uniform(0, 100)
            start_center = [
                self.res[0] // 2 + x_v * m,
                self.res[1] // 2 + y_v * m]
            end_center = [
                self.res[0] // 2 + x_v * m,
                self.res[1] // 2 + y_v * m]

            self.bg_beams.append(animations.BackgroundBeam(
                [x_v, y_v],
                [color, color, color],
                randint(10, 15),
                start_center,
                end_center)
            )

        for b in self.bg_beams:
            b.draw(self.Screen)
            b.modify()
            if len(self.bg_beams) > 45:
                self.bg_beams.pop(0)

        for anim in self.active_animations:
            anim.draw(self.Screen)
            if anim.radius > self.res[0] * 1.5:
                self.active_animations.remove(anim)

    def draw_level_menu(self):
        self.draw_bg()

        pygame.draw.polygon(self.Screen, self.l_arr_color, [
            [75, self.res[1] // 2],
            [125, self.res[1] // 2 + 75],
            [125, self.res[1] // 2 - 75]
        ])
        pygame.draw.polygon(self.Screen, self.r_arr_color, [
            [self.res[0] - 75, self.res[1] // 2],
            [self.res[0] - 125, self.res[1] // 2 + 75],
            [self.res[0] - 125, self.res[1] // 2 - 75]
        ])

        self.Screen.blit(self.level_menu_index, self.level_menu_index_center)
        for button in self.level_menu_buttons:
            button.draw(self.Screen)

        pygame.display.update()

    def draw_pause(self):
        self.draw_bg()

        self.Screen.blit(self.pause_title, self.pause_title_center)
        for button in self.pause_menu_buttons:
            button.draw(self.Screen)

        pygame.display.update()

    def draw_menu(self):
        self.draw_bg()
        self.draw_board()

        self.Screen.blit(self.title_text, self.title_text_center)
        for button in self.main_menu_buttons:
            button.draw(self.Screen)

        pygame.display.update()

    def draw_game_over(self):
        self.draw_bg()

        self.Screen.blit(self.game_over_text_1, self.game_over_text_1_center)
        self.Screen.blit(self.game_over_text_2, self.game_over_text_2_center)
        self.Screen.blit(self.game_over_stats, self.game_over_stats_center)
        self.try_again_button.draw(self.Screen)

        pygame.display.update()

    def draw_credits(self):
        self.draw_bg()
        self.Screen.blit(
            self.last_credits_text,
            [self.music_credits_text_center[0] + self.parallax_move[0] / 2,
             self.music_credits_text_center[1] + self.parallax_move[1] / 2]
        )
        self.Screen.blit(
            self.last_1_credits_text,
            [self.art_credits_text_center[0] + self.parallax_move[0] / 2,
             self.art_credits_text_center[1] + self.parallax_move[1] / 2]
        )
        self.Screen.blit(
            self.dev_credits_text,
            [self.dev_credits_text_center[0] + self.parallax_move[0] / 2,
             self.dev_credits_text_center[1] + self.parallax_move[1] / 2]
        )

        pygame.display.update()

    def draw_game(self):
        self.draw_bg()
        self.draw_board()

        if self.buy_menu_open:
            pygame.draw.rect(
                self.Screen,
                [100, 100, 100],
                (self.buy_menu_pos[0],
                 self.buy_menu_pos[1],
                 50 * self.buy_menu_width,
                 50)
            )
            pygame.draw.rect(
                self.Screen,
                [80, 80, 80],
                (self.buy_menu_pos[0] + 5,
                 self.buy_menu_pos[1] + 5,
                 50 * self.buy_menu_width - 10,
                 40)
            )

            for tr in self.available_turrets:
                tr.draw(self.Screen)

            self.cost_center = self.cost_text.get_rect(
                center=(
                    self.res[0] // 2 + self.parallax_move[0] / 7,
                    self.COST_Y + self.parallax_move[1] / 7)
            )
            self.notif_text_center = self.notif_text.get_rect(
                center=(
                    self.res[0] // 2 + self.parallax_move[0] / 7,
                    self.NOTIF_Y + self.parallax_move[1] / 7)
            )
            self.tower_info_text_center = self.tower_info_text.get_rect(
                center=(
                    self.res[0] // 2 + self.parallax_move[0] / 7,
                    self.INFO_Y + self.parallax_move[1] / 7)
            )
            self.Screen.blit(self.cost_text, self.cost_center)
            self.Screen.blit(self.notif_text, self.notif_text_center)
            self.Screen.blit(self.tower_info_text, self.tower_info_text_center)

        elif self.turret_menu_open:
            pygame.draw.rect(
                self.Screen,
                [100, 100, 100],
                (self.turret_menu_pos[0],
                 self.turret_menu_pos[1],
                 50 * self.turret_menu_width,
                 50)
            )
            pygame.draw.rect(
                self.Screen,
                [80, 80, 80],
                (self.turret_menu_pos[0] + 5,
                 self.turret_menu_pos[1] + 5,
                 50 * self.turret_menu_width - 10,
                 40)
            )

            for btn in self.turret_menu_buttons:
                self.Screen.blit(btn[2], btn[1])

            self.cost_center = self.cost_text.get_rect(
                center=(
                    self.res[0] // 2 + self.parallax_move[0] / 7,
                    self.COST_Y + self.parallax_move[1] / 7)
            )
            self.notif_text_center = self.notif_text.get_rect(
                center=(
                    self.res[0] // 2 + self.parallax_move[0] / 7,
                    self.NOTIF_Y + self.parallax_move[1] / 7)
            )
            self.Screen.blit(self.cost_text, self.cost_center)
            self.Screen.blit(self.notif_text, self.notif_text_center)

        self.Screen.blit(
            self.money_text,
            (
                30 + self.parallax_move[0] / 5,
                20 + self.parallax_move[1] / 5)
        )
        self.Screen.blit(
            self.health_text,
            (
                30 + self.parallax_move[0] / 5,
                80 + self.parallax_move[1] / 5)
        )
        self.Screen.blit(
            self.wave_text,
            (
                self.res[0] - 30 - 25 * self.wave_text_width + self.parallax_move[0] / 5,
                20 + self.parallax_move[1] / 5)
        )
        if self.selected_tile in self.tiles and not self.buy_menu_open and not self.turret_menu_open:
            self.Screen.blit(self.indicator, self.selected_tile)

        pygame.display.update()


g = Game()
g.play_intro()

pygame.quit()
