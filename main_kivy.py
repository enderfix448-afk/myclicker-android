"""
My Clicker для Android (Kivy версия)
Запуск на ПК: python main_kivy.py
Сборка для Android: buildozer android debug
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.storage.jsonstore import JsonStore
import random
import os
import time

# Путь для сохранения
try:
    from android.storage import app_storage_path
    DATA_PATH = app_storage_path()
except ImportError:
    DATA_PATH = os.path.dirname(os.path.abspath(__file__))

SAVE_FILE = os.path.join(DATA_PATH, 'save.json')


class AchievementPopup(Popup):
    pass


class MyClickerApp(App):
    score = NumericProperty(0)
    click_power = NumericProperty(1)
    auto_clicks = NumericProperty(0)
    is_god_mode = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.achievements = [False, False, False, False]
        self.jackpot_achievement = False
        self.last_event_time = 0
        self.is_event_active = False
        self.event_clicks = 0
        self.event_moves = 0
        
    def build(self):
        # Полноэкранный режим
        Window.fullscreen = 'auto'
        
        # Загрузка сохранения
        self.load_game()
        
        # Основной layout
        self.layout = FloatLayout()
        
        # Фон
        with self.layout.canvas.before:
            Color(1, 1, 1, 1)
            try:
                self.bg = Rectangle(source='fon.jpg', pos=self.layout.pos, size=self.layout.size)
                self.layout.bind(pos=self.update_bg, size=self.update_bg)
            except:
                pass
        
        # Счёт
        self.score_label = Label(
            text=f'Очки: {int(self.score)}',
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            pos=(20, Window.height - 60),
            size_hint=(None, None),
            size=(300, 50),
            halign='left'
        )
        self.layout.add_widget(self.score_label)
        
        # Главная кнопка (спрайт)
        self.click_button = Button(
            text='',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint=(None, None),
            size=(min(Window.width, Window.height) * 0.5, min(Window.width, Window.height) * 0.5)
        )
        
        # Загрузка спрайта
        try:
            self.click_button.background_normal = 'Sprite-0001.png'
            self.click_button.background_down = 'sprite1.png'
        except:
            self.click_button.text = '🎮'
            self.click_button.font_size = '80sp'
        
        self.click_button.bind(on_press=self.on_click)
        self.layout.add_widget(self.click_button)
        
        # Кнопка магазина
        self.shop_button = Button(
            text='🛒 Магазин',
            font_size='20sp',
            bold=True,
            pos_hint={'center_x': 0.5, 'bottom': 0.05},
            size_hint=(None, None),
            size=(220, 70),
            background_color=(0.2, 0.6, 0.2, 1)
        )
        self.shop_button.bind(on_press=self.open_shop)
        self.layout.add_widget(self.shop_button)
        
        # Кнопка ачивок (кубок)
        self.ach_button = Button(
            text='🏆',
            font_size='40sp',
            pos_hint={'left': 0.02, 'bottom': 0.05},
            size_hint=(None, None),
            size=(60, 60),
            background_color=(0.8, 0.6, 0, 1)
        )
        self.ach_button.bind(on_press=self.show_achievements)
        self.layout.add_widget(self.ach_button)
        
        # Кнопка админа (секретная)
        self.admin_button = Button(
            text='⚙️',
            font_size='20sp',
            pos_hint={'right': 0.02, 'top': 0.02},
            size_hint=(None, None),
            size=(50, 50),
            background_color=(0.3, 0.3, 0.3, 0.5)
        )
        self.admin_button.bind(on_press=self.open_admin)
        self.layout.add_widget(self.admin_button)
        
        # Авто-сохранение каждые 10 секунд
        Clock.schedule_interval(self.auto_save, 10)
        
        # Автоклики каждую секунду
        Clock.schedule_interval(self.auto_click, 1)
        
        return self.layout
    
    def update_bg(self, instance, value):
        if hasattr(self, 'bg'):
            self.bg.pos = instance.pos
            self.bg.size = instance.size
    
    def on_click(self, instance):
        current_time = time.time() * 1000
        
        # Джекпот (1/5000)
        if random.randint(1, 5000) == 1:
            self.score += 100000
            self.show_notification('!!! JACKPOT +100.000 !!!', (1, 0.8, 0, 1))
            if not self.jackpot_achievement:
                self.jackpot_achievement = True
                self.show_notification('АЧИВКА: ДЖЕКПОТ!', (0, 1, 0, 1))
        
        self.score += self.click_power
        self.update_score_label()
        self.check_achievements()
        
        # Шанс на ивент (1/60 после кулдауна 25 сек)
        if current_time - self.last_event_time > 25000:
            if random.randint(1, 60) == 1:
                self.start_event()
    
    def start_event(self):
        self.is_event_active = True
        self.event_clicks = 0
        self.event_moves = 0
        self.show_notification('ИВЕНТ: КЛИКНИ 3 РАЗА!', (1, 0, 0, 1))
    
    def check_achievements(self):
        thresholds = [1000, 10000, 100000, 1000000]
        names = ['1K очков!', '10K очков!', '100K очков!', '1M очков!']
        
        for i, threshold in enumerate(thresholds):
            if self.score >= threshold and not self.achievements[i]:
                self.achievements[i] = True
                self.show_notification(f'АЧИВКА: {names[i]}', (0, 1, 0, 1))
    
    def show_notification(self, text, color=(1, 1, 1, 1)):
        popup = Popup(
            title='Уведомление',
            content=Label(text=text, font_size='24sp', bold=True, color=color),
            size_hint=(0.8, 0.25),
            auto_dismiss=True
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def update_score_label(self):
        self.score_label.text = f'Очки: {int(self.score)}'
    
    def open_shop(self, instance):
        shop_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        
        # Заголовок
        title = Label(text='МАГАЗИН', font_size='28sp', bold=True, size_hint=(1, 0.2))
        shop_layout.add_widget(title)
        
        # Расчёт цен
        if self.is_god_mode:
            click_cost = 1
            auto_cost = 1
        else:
            click_cost = int(100 * (1.2 ** (self.click_power - 1)))
            auto_cost = int(1000 * (1.2 ** self.auto_clicks))
        
        # Кнопка улучшения клика
        click_btn = Button(
            text=f'Сила клика +1\n[ref=price]Цена: {click_cost}[/ref]',
            font_size='20sp',
            size_hint=(1, 0.3),
            background_color=(0.2, 0.5, 0.2, 1),
            markup=True
        )
        click_btn.bind(on_press=lambda x: self.buy_click(click_cost))
        shop_layout.add_widget(click_btn)
        
        # Кнопка автоклика
        auto_btn = Button(
            text=f'Автоклик +1\n[ref=price]Цена: {auto_cost}[/ref]',
            font_size='20sp',
            size_hint=(1, 0.3),
            background_color=(0.2, 0.2, 0.5, 1),
            markup=True
        )
        auto_btn.bind(on_press=lambda x: self.buy_auto(auto_cost))
        shop_layout.add_widget(auto_btn)
        
        # Кнопка закрытия
        close_btn = Button(
            text='Закрыть',
            font_size='20sp',
            size_hint=(1, 0.2),
            background_color=(0.5, 0.2, 0.2, 1)
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        shop_layout.add_widget(close_btn)
        
        popup = Popup(title='', content=shop_layout, size_hint=(0.9, 0.75), background_color=(0, 0, 0, 0.8))
        popup.open()
    
    def buy_click(self, cost):
        if self.score >= cost:
            self.score -= cost
            self.click_power += 1
            self.update_score_label()
            self.show_notification(f'Куплено! Сила клика: {self.click_power}', (0, 1, 0, 1))
        else:
            self.show_notification('Недостаточно очков!', (1, 0, 0, 1))
    
    def buy_auto(self, cost):
        if self.score >= cost:
            self.score -= cost
            self.auto_clicks += 1
            self.update_score_label()
            self.show_notification(f'Куплено! Автокликов: {self.auto_clicks}', (0, 1, 0, 1))
        else:
            self.show_notification('Недостаточно очков!', (1, 0, 0, 1))
    
    def auto_click(self, dt):
        if self.auto_clicks > 0:
            self.score += self.auto_clicks
            self.update_score_label()
    
    def auto_save(self, dt):
        self.save_game()
        return True
    
    def save_game(self):
        try:
            store = JsonStore(SAVE_FILE)
            store.put('game',
                score=int(self.score),
                click_power=self.click_power,
                auto_clicks=self.auto_clicks,
                achievements=','.join([str(int(a)) for a in self.achievements]),
                jackpot_achievement=int(self.jackpot_achievement),
                is_god_mode=int(self.is_god_mode)
            )
            print('Игра сохранена')
        except Exception as e:
            print(f'Ошибка сохранения: {e}')
    
    def load_game(self):
        try:
            store = JsonStore(SAVE_FILE)
            if store.exists('game'):
                data = store.get('game')
                self.score = data.get('score', 0)
                self.click_power = data.get('click_power', 1)
                self.auto_clicks = data.get('auto_clicks', 0)
                
                ach_str = data.get('achievements', '0,0,0,0')
                self.achievements = [bool(int(x)) for x in ach_str.split(',')]
                
                self.jackpot_achievement = bool(data.get('jackpot_achievement', 0))
                self.is_god_mode = bool(data.get('is_god_mode', 0))
                
                print('Игра загружена')
        except Exception as e:
            print(f'Ошибка загрузки: {e}')
    
    def show_achievements(self, instance):
        ach_layout = BoxLayout(orientation='vertical', spacing=15, padding=30)
        
        title = Label(text='🏆 АЧИВКИ', font_size='28sp', bold=True, size_hint=(1, 0.15), color=(1, 0.8, 0, 1))
        ach_layout.add_widget(title)
        
        all_names = ['1K очков!', '10K очков!', '100K очков!', '1M очков!', 'ДЖЕКПОТ!']
        all_unlocked = self.achievements + [self.jackpot_achievement]
        
        for name, unlocked in zip(all_names, all_unlocked):
            color = (0, 1, 0, 1) if unlocked else (0.4, 0.4, 0.4, 1)
            status = '✓' if unlocked else '✗'
            ach_label = Label(
                text=f'{status} {name}',
                font_size='18sp',
                size_hint=(1, 0.12),
                color=color,
                halign='left'
            )
            ach_layout.add_widget(ach_label)
        
        close_btn = Button(
            text='Закрыть',
            font_size='20sp',
            size_hint=(1, 0.15),
            background_color=(0.5, 0.2, 0.2, 1)
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        ach_layout.add_widget(close_btn)
        
        popup = Popup(title='', content=ach_layout, size_hint=(0.85, 0.7), background_color=(0, 0, 0, 0.85))
        popup.open()
    
    def open_admin(self, instance):
        admin_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        
        title = Label(text='АДМИН ПАНЕЛЬ', font_size='24sp', bold=True, size_hint=(1, 0.2), color=(1, 0, 0, 1))
        admin_layout.add_widget(title)
        
        info = Label(
            text='Введите пароль:\n• EndGamesTop - сброс\n• EndGamesBad - читы',
            font_size='16sp',
            size_hint=(1, 0.25),
            halign='center'
        )
        admin_layout.add_widget(info)
        
        from kivy.uix.textinput import TextInput
        self.admin_input = TextInput(
            password=True,
            multiline=False,
            font_size='20sp',
            size_hint=(1, 0.15),
            halign='center'
        )
        admin_layout.add_widget(self.admin_input)
        
        submit_btn = Button(
            text='Войти',
            font_size='20sp',
            size_hint=(1, 0.15),
            background_color=(0.2, 0.5, 0.2, 1)
        )
        submit_btn.bind(on_press=self.submit_admin)
        admin_layout.add_widget(submit_btn)
        
        close_btn = Button(
            text='Отмена',
            font_size='20sp',
            size_hint=(1, 0.15),
            background_color=(0.5, 0.2, 0.2, 1)
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        admin_layout.add_widget(close_btn)
        
        popup = Popup(title='', content=admin_layout, size_hint=(0.8, 0.6), background_color=(0.2, 0, 0, 0.9))
        popup.open()
    
    def submit_admin(self, instance):
        password = self.admin_input.text
        
        if password == 'EndGamesTop':
            self.score = 0
            self.click_power = 1
            self.auto_clicks = 0
            self.is_god_mode = False
            self.show_notification('Прогресс сброшен', (1, 1, 1, 1))
        elif password == 'EndGamesBad':
            self.score = 1000000
            self.click_power = 100
            self.auto_clicks = 100
            self.achievements = [True, True, True, True]
            self.jackpot_achievement = True
            self.is_god_mode = True
            self.show_notification('ЧИТЫ АКТИВИРОВАНЫ!', (0, 1, 0, 1))
        
        self.update_score_label()
        self.save_game()
        
 # Закрыть popup
        for widget in self.layout.children:
            if isinstance(widget, Popup):
                widget.dismiss()
                break
    
    def on_stop(self):
        self.save_game()


if __name__ == '__main__':
    MyClickerApp().run()
