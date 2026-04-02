import pygame
import sys
import os
import random

# --- ОБНОВЛЕННАЯ ЛОГИКА СОХРАНЕНИЯ (Android-safe) ---
# Используем abspath, чтобы Android точно нашел путь к внутренней памяти приложения
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_PATH, "save.txt")

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Загрузка звука клика
CLICK_SOUND = os.path.join(BASE_PATH, "button-click-short-ringing-close-dry.mp3")
try:
    click_sound = pygame.mixer.Sound(CLICK_SOUND)
    click_sound.set_volume(0.5)
except:
    click_sound = None

# Настройка экрана под устройство (Full HUD для мобилок)
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("My Clicker Mobile Pro")


def load_game():
    # При каждом запуске игра начинается с нуля, ачивки загружаются
    achievements = [False, False, False, False]  # 1K, 10K, 100K, 1M
    jackpot_ach = False
    god_mode = False
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = f.read().strip().split(',')
                if len(data) >= 4:
                    achievements = [data[3] == '1', data[4] == '1' if len(data) > 4 else False,
                                   data[5] == '1' if len(data) > 5 else False,
                                   data[6] == '1' if len(data) > 6 else False]
                    jackpot_ach = data[7] == '1' if len(data) > 7 else False
                    god_mode = data[8] == '1' if len(data) > 8 else False
        except Exception as e:
            print(f"Ошибка загрузки ачивок: {e}")
    return 0, 1, 0, achievements, jackpot_ach, god_mode  # Очки, Сила клика, Автоклики, Ачивки, Джекпот-ачивка, God-режим


def save_game(s, p, a, ach=None, jackpot_ach=False, god_mode=False):
    try:
        with open(SAVE_FILE, "w") as f:
            if ach:
                f.write(f"{s},{p},{a},{int(ach[0])},{int(ach[1])},{int(ach[2])},{int(ach[3])},{int(jackpot_ach)},{int(god_mode)}")
            else:
                f.write(f"{s},{p},{a},0,0,0,0,0,0")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")


# --- ЗАГРУЗКА РЕСУРСОВ ---
def load_image(name, size):
    try:
        img = pygame.image.load(os.path.join(BASE_PATH, name)).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size)
        surf.fill((random.randint(50, 150), 100, 150))
        return surf


# Масштабируемые размеры под экран телефона
char_size = int(min(WIDTH, HEIGHT) * 0.7)
background = load_image("fon.jpg", (WIDTH, HEIGHT))
sprites = [
    load_image("Sprite-0001.png", (char_size, char_size)),
    load_image("sprite1.png", (char_size, char_size)),
    load_image("sprite4.png", (char_size, char_size))
]

admin_icon = pygame.transform.scale(sprites[0], (50, 50))
admin_rect = admin_icon.get_rect(topright=(WIDTH - 20, 20))

# Состояние игры
score, click_power, auto_clicks, achievements, jackpot_achievement, is_god_mode = load_game()
font = pygame.font.SysFont("Arial", int(HEIGHT * 0.035), bold=True)
big_font = pygame.font.SysFont("Arial", int(HEIGHT * 0.06), bold=True)

shop_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT - 140, 240, 90)
is_shop_open = False
is_admin_mode = False
admin_input = ""
is_exit_dialog = False  # Флаг диалога выхода
is_achievements_screen = False  # Флаг экрана ачивок
is_god_mode = False  # Режим бога (все по 1 очку)

# Кнопка ачивок (кубок)
trophy_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
pygame.draw.circle(trophy_icon, (255, 215, 0), (20, 20), 18)
pygame.draw.circle(trophy_icon, (200, 170, 0), (20, 20), 18, 3)
pygame.draw.polygon(trophy_icon, (255, 215, 0), [(10, 15), (30, 15), (25, 30), (15, 30)])
trophy_rect = trophy_icon.get_rect(bottomleft=(30, HEIGHT - 30))

# Ачивки
ACHIEVEMENTS_THRESHOLDS = [1000, 10000, 100000, 1000000]
ACHIEVEMENTS_NAMES = ["1000 очков!", "10000 очков!", "100000 очков!", "1000000 очков!"]
achievement_notification = None
achievement_notify_timer = 0
jackpot_achievement = False  # Ачивка за джекпот

current_frame, last_update = 0, 0
sprite_rect = sprites[0].get_rect(center=(WIDTH // 2, HEIGHT // 2))

# Ивенты
last_event_time = 0
COOLDOWN = 25000
is_event_active = False
current_event_clicks, current_event_moves = 0, 0
event_circle_pos = [0, 0]
event_radius = int(WIDTH * 0.045)  # Зона клика (уменьшена в 2 раза)

jackpot_flash_timer = 0
is_powerup_active = False
powerup_end_time = 0

# Таймер для автокликов
AUTO_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(AUTO_EVENT, 1000)
clock = pygame.time.Clock()

while True:
    screen.blit(background, (0, 0))
    current_time = pygame.time.get_ticks()

    click_upgrade_cost = 1 if is_god_mode else int(100 * (1.2 ** (click_power - 1)))
    auto_upgrade_cost = 1 if is_god_mode else int(1000 * (1.2 ** auto_clicks))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game(score, click_power, auto_clicks, achievements, jackpot_achievement, is_god_mode)
            pygame.quit();
            sys.exit()

        if event.type == AUTO_EVENT:
            score += auto_clicks
            # Авто-сохранение каждые 10 секунд (на всякий случай)
            if pygame.time.get_ticks() % 10000 < 1000:
                save_game(score, click_power, auto_clicks, achievements, jackpot_achievement, is_god_mode)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if is_exit_dialog:
                    is_exit_dialog = False
                elif not is_shop_open and not is_admin_mode:
                    is_exit_dialog = True
                continue

        if is_admin_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if admin_input == "EndGamesTop":
                        score, click_power, auto_clicks = 0, 1, 0
                        is_god_mode = False
                    elif admin_input == "EndGamesBad":
                        score = 1000000
                        click_power = 100
                        auto_clicks = 100
                        achievements = [True, True, True, True]
                        jackpot_achievement = True
                        is_god_mode = True
                    is_admin_mode = False;
                    admin_input = ""
                elif event.key == pygame.K_BACKSPACE:
                    admin_input = admin_input[:-1]
                else:
                    admin_input += event.unicode
            continue

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            # Обработка клика по диалогу выхода
            if is_exit_dialog:
                yes_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 120, 50)
                no_rect = pygame.Rect(WIDTH // 2 + 30, HEIGHT // 2 + 50, 120, 50)
                if yes_rect.collidepoint(pos):
                    save_game(score, click_power, auto_clicks, achievements, jackpot_achievement, is_god_mode)
                    pygame.quit()
                    sys.exit()
                if no_rect.collidepoint(pos):
                    is_exit_dialog = False
                continue

            if is_shop_open:
                if shop_rect.collidepoint(pos): is_shop_open = False
                if WIDTH * 0.1 < pos[0] < WIDTH * 0.9:
                    if HEIGHT * 0.3 < pos[1] < HEIGHT * 0.45 and score >= click_upgrade_cost:
                        score -= click_upgrade_cost;
                        click_power += 1
                    if HEIGHT * 0.5 < pos[1] < HEIGHT * 0.65 and score >= auto_upgrade_cost:
                        score -= auto_upgrade_cost;
                        auto_clicks += 1
                continue

            if admin_rect.collidepoint(pos): is_admin_mode = True; admin_input = ""; continue
            if shop_rect.collidepoint(pos): is_shop_open = True; continue
            
            # Кнопка ачивок
            if trophy_rect.collidepoint(pos):
                is_achievements_screen = not is_achievements_screen
                continue

            # Ивент "Догони"
            if is_event_active:
                dx, dy = pos[0] - event_circle_pos[0], pos[1] - event_circle_pos[1]
                if (dx ** 2 + dy ** 2) ** 0.5 <= event_radius:
                    score += 5 * click_power
                    current_event_clicks += 1
                    if current_event_clicks >= 3:
                        current_event_clicks = 0
                        current_event_moves += 1
                        event_circle_pos = [random.randint(100, WIDTH - 100), random.randint(150, HEIGHT - 150)]
                        if current_event_moves >= 5:
                            is_event_active = False;
                            last_event_time = current_time
                continue

            # Обычный клик по лицу
            if sprite_rect.collidepoint(pos):
                score += (click_power * 10) if is_powerup_active else click_power
                current_frame = 0;
                last_update = current_time

                # Воспроизведение звука клика
                if click_sound:
                    click_sound.play()
                
                # Проверка ачивок
                for i, threshold in enumerate(ACHIEVEMENTS_THRESHOLDS):
                    if score >= threshold and not achievements[i]:
                        achievements[i] = True
                        achievement_notification = ACHIEVEMENTS_NAMES[i]
                        achievement_notify_timer = current_time + 3000

                # Шанс на джекпот (1 к 5000)
                if random.randint(1, 5000) == 1:
                    score += 100000
                    jackpot_flash_timer = current_time + 2500
                    
                    # Ачивка за джекпот
                    if not jackpot_achievement:
                        jackpot_achievement = True
                        achievement_notification = "ДЖЕКПОТ!"
                        achievement_notify_timer = current_time + 3000

                # Шанс на ивент
                if current_time - last_event_time > COOLDOWN:
                    if random.randint(1, 60) == 1:
                        is_event_active = True
                        current_event_clicks, current_event_moves = 0, 0
                        event_circle_pos = [WIDTH // 2, HEIGHT // 2]

    # Визуальный эффект Джекпота
    if current_time < jackpot_flash_timer:
        txt = big_font.render("!!! JACKPOT +100.000 !!!", True, (255, 215, 0))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, sprite_rect.top - 80))

    # Уведомление об ачивке
    if achievement_notification and current_time < achievement_notify_timer:
        ach_txt = big_font.render(f"АЧИВКА: {achievement_notification}", True, (0, 255, 0))
        screen.blit(ach_txt, (WIDTH // 2 - ach_txt.get_width() // 2, sprite_rect.top - 120))
    elif achievement_notification and current_time >= achievement_notify_timer:
        achievement_notification = None

    # Отрисовка главного персонажа
    if not is_event_active:
        if current_frame < len(sprites) - 1 and current_time - last_update > 60:
            current_frame += 1
        screen.blit(sprites[current_frame], sprite_rect)
        
        # Надпись о бусте x10
        if is_powerup_active:
            boost_txt = font.render("x10 КЛИКОВ!", True, (255, 255, 0))
            screen.blit(boost_txt, (WIDTH // 2 - boost_txt.get_width() // 2, sprite_rect.top - 40))
    else:
        # Рисуем цель ивента
        pygame.draw.circle(screen, (255, 255, 255), event_circle_pos, event_radius + 4)
        pygame.draw.circle(screen, (255, 50, 0), event_circle_pos, event_radius)
        t = font.render(f"ЛОВИ! {current_event_moves}/5", True, (255, 255, 255))
        screen.blit(t, (WIDTH // 2 - t.get_width() // 2, 70))

    # Интерфейс
    screen.blit(font.render(f"Очки: {score}", True, (255, 255, 255)), (40, 40))
    pygame.draw.rect(screen, (70, 70, 70), shop_rect, border_radius=20)
    pygame.draw.rect(screen, (200, 200, 200), shop_rect, width=3, border_radius=20)
    sh_t = font.render("МАГАЗИН", True, (255, 255, 255))
    screen.blit(sh_t, (shop_rect.centerx - sh_t.get_width() // 2, shop_rect.centery - sh_t.get_height() // 2))
    screen.blit(admin_icon, admin_rect)
    screen.blit(trophy_icon, trophy_rect)  # Кнопка ачивок

    # Окно магазина
    if is_shop_open:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA);
        overlay.fill((0, 0, 0, 235))
        screen.blit(overlay, (0, 0))
        # Кнопка Клик
        pygame.draw.rect(screen, (40, 130, 40), (WIDTH * 0.1, HEIGHT * 0.3, WIDTH * 0.8, HEIGHT * 0.15),
                         border_radius=20)
        t1 = font.render(f"Сила клика +1 | Цена: {click_upgrade_cost}", True, (255, 255, 255))
        screen.blit(t1, (WIDTH // 2 - t1.get_width() // 2, HEIGHT * 0.35))
        # Кнопка Авто
        pygame.draw.rect(screen, (40, 40, 130), (WIDTH * 0.1, HEIGHT * 0.5, WIDTH * 0.8, HEIGHT * 0.15),
                         border_radius=20)
        t2 = font.render(f"Автокликер +1 | Цена: {auto_upgrade_cost}", True, (255, 255, 255))
        screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT * 0.55))

    # Окно админа
    if is_admin_mode:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA);
        overlay.fill((20, 0, 0, 250))
        screen.blit(overlay, (0, 0))
        m = font.render("ВВЕДИТЕ ПАРОЛЬ:", True, (255, 255, 255))
        screen.blit(m, (WIDTH // 2 - m.get_width() // 2, HEIGHT * 0.35))
        stars = big_font.render("*" * len(admin_input), True, (255, 0, 0))
        screen.blit(stars, (WIDTH // 2 - stars.get_width() // 2, HEIGHT * 0.45))

    # Диалог выхода
    if is_exit_dialog:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        # Окно диалога
        dialog_rect = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 100, 400, 200)
        pygame.draw.rect(screen, (50, 50, 50), dialog_rect, border_radius=15)
        pygame.draw.rect(screen, (200, 200, 200), dialog_rect, width=3, border_radius=15)
        # Текст
        q_text = big_font.render("Выйти из игры?", True, (255, 255, 255))
        screen.blit(q_text, (WIDTH // 2 - q_text.get_width() // 2, HEIGHT // 2 - 50))
        # Кнопки
        yes_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 50, 120, 50)
        no_rect = pygame.Rect(WIDTH // 2 + 30, HEIGHT // 2 + 50, 120, 50)
        pygame.draw.rect(screen, (200, 50, 50), yes_rect, border_radius=10)
        pygame.draw.rect(screen, (50, 200, 50), no_rect, border_radius=10)
        yes_text = font.render("ДА", True, (255, 255, 255))
        no_text = font.render("НЕТ", True, (255, 255, 255))
        screen.blit(yes_text, (yes_rect.centerx - yes_text.get_width() // 2, yes_rect.centery - yes_text.get_height() // 2))
        screen.blit(no_text, (no_rect.centerx - no_text.get_width() // 2, no_rect.centery - no_text.get_height() // 2))

    # Экран ачивок
    if is_achievements_screen:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        # Заголовок
        title = big_font.render("АЧИВКИ", True, (255, 215, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 80))
        # Список ачивок
        all_achievements = ACHIEVEMENTS_NAMES + ["ДЖЕКПОТ!"]
        all_unlocked = achievements + [jackpot_achievement]
        for i, (name, unlocked) in enumerate(zip(all_achievements, all_unlocked)):
            y_pos = 160 + i * 70
            color = (0, 255, 0) if unlocked else (100, 100, 100)
            status = "✓" if unlocked else "✗"
            ach_text = font.render(f"{status} {name}", True, color)
            screen.blit(ach_text, (WIDTH // 2 - ach_text.get_width() // 2, y_pos))
        # Кнопка закрытия
        close_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 120, 200, 60)
        pygame.draw.rect(screen, (200, 50, 50), close_rect, border_radius=15)
        close_text = font.render("ЗАКРЫТЬ", True, (255, 255, 255))
        screen.blit(close_text, (close_rect.centerx - close_text.get_width() // 2, close_rect.centery - close_text.get_height() // 2))
        # Проверка клика по кнопке закрытия
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()
            if close_rect.collidepoint(mouse_pos):
                is_achievements_screen = False
                pygame.time.wait(200)  # Задержка чтобы не спамить

    pygame.display.flip()
    clock.tick(60)