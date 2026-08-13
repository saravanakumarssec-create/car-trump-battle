import json
import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

try:
    from server_config import SERVER_URL
except ImportError:
    SERVER_URL = "wss://REPLACE_WITH_YOUR_RENDER_SERVICE.onrender.com"


class NetworkClient:
    def __init__(self, app):
        self.app = app
        self.ws = None
        self.running = False

    def connect(self):
        try:
            import websocket
            self.ws = websocket.create_connection(SERVER_URL, timeout=12)
            self.running = True
            threading.Thread(target=self.receive_loop, daemon=True).start()
        except Exception as exc:
            self.running = False
            Clock.schedule_once(lambda dt, e=str(exc): self.app.network_error(e), 0)

    def send(self, data):
        if not self.running or self.ws is None:
            return
        try:
            self.ws.send(json.dumps(data))
        except Exception:
            self.running = False
            Clock.schedule_once(lambda dt: self.app.network_error("Connection lost."), 0)

    def receive_loop(self):
        try:
            while self.running:
                raw = self.ws.recv()
                if raw is None:
                    break
                try:
                    msg = json.loads(raw)
                except (TypeError, json.JSONDecodeError):
                    continue
                Clock.schedule_once(lambda dt, m=msg: self.app.handle_message(m), 0)
        except Exception:
            pass
        self.running = False
        Clock.schedule_once(lambda dt: self.app.network_error("Connection closed."), 0)

    def close(self):
        self.running = False
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass

class PlayerCard(BoxLayout):
    def __init__(self, card, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 8
        self.spacing = 2
        self.size_hint = (0.48, 0.48)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.52}
        with self.canvas.before:
            Color(0.035, 0.055, 0.12, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[18])
            Color(0.15, 0.65, 1, 1)
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 18), width=2.5)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.add_widget(Label(text="CARD #" + str(card["id"]), font_size=10, bold=True, size_hint_y=0.10))
        self.add_widget(Label(text=str(card["name"]).upper(), font_size=17, bold=True, size_hint_y=0.16))
        image_path = card.get("image", "")
        if image_path and os.path.exists(image_path):
            self.add_widget(Image(source=image_path, allow_stretch=True, keep_ratio=True, size_hint_y=0.40))
        else:
            self.add_widget(Label(text="CAR", font_size=18, bold=True, size_hint_y=0.40))
        self.add_widget(Label(text="ATTACK  " + str(card["attack"]), font_size=14, bold=True, size_hint_y=0.13))
        self.add_widget(Label(text="DEFENCE " + str(card["defence"]), font_size=14, bold=True, size_hint_y=0.13))
        self.add_widget(Label(text="YOUR CARD", font_size=9, bold=True, size_hint_y=0.08))

    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, 18)


class OnlineAndroidGame(App):
    def build(self):
        self.title = "Car Trump Battle"
        self.player_number = -1
        self.busy = True
        self.my_turn = False
        self.current_deck = []
        self.card_widget = None

        root = FloatLayout()
        with root.canvas.before:
            Color(0.015, 0.025, 0.07, 1)
            self.background = RoundedRectangle(pos=root.pos, size=root.size)
        root.bind(pos=self.update_background, size=self.update_background)

        self.title_label = Label(text="CAR TRUMP BATTLE", font_size=23, bold=True, color=(0.2, 0.8, 1, 1), size_hint=(1, 0.08), pos_hint={"x": 0, "top": 1})
        root.add_widget(self.title_label)
        self.status_label = Label(text="CONNECTING...", font_size=12, bold=True, color=(0.3, 1, 0.5, 1), size_hint=(1, 0.045), pos_hint={"x": 0, "top": 0.91})
        root.add_widget(self.status_label)
        self.round_label = Label(text="ROUND --", font_size=13, bold=True, size_hint=(0.5, 0.045), pos_hint={"x": 0, "top": 0.865})
        root.add_widget(self.round_label)
        self.cards_label = Label(text="YOU: --   OPPONENT: --", font_size=13, bold=True, size_hint=(0.55, 0.045), pos_hint={"x": 0.45, "top": 0.865})
        root.add_widget(self.cards_label)

        self.turn_label = Label(text="", font_size=14, bold=True, size_hint=(1, 0.055), pos_hint={"x": 0, "top": 0.81})
        root.add_widget(self.turn_label)

        self.message_label = Label(text="CONNECTING TO SERVER...", font_size=15, bold=True, size_hint=(1, 0.07), pos_hint={"x": 0, "y": 0.18})
        root.add_widget(self.message_label)

        self.view_cards_button = Button(text="VIEW MY CARDS", font_size=13, bold=True, background_normal="", background_color=(0.10, 0.28, 0.55, 1), size_hint=(0.36, 0.06), pos_hint={"x": 0.32, "y": 0.12})
        self.view_cards_button.bind(on_press=lambda instance: self.show_my_cards())
        root.add_widget(self.view_cards_button)

        self.attack_button = Button(text="ATTACK", font_size=16, bold=True, background_normal="", background_color=(0.05, 0.45, 0.95, 1), size_hint=(0.38, 0.075), pos_hint={"x": 0.08, "y": 0.035})
        self.attack_button.bind(on_press=lambda instance: self.choose("attack"))
        root.add_widget(self.attack_button)

        self.defence_button = Button(text="DEFENCE", font_size=16, bold=True, background_normal="", background_color=(0.90, 0.12, 0.08, 1), size_hint=(0.38, 0.075), pos_hint={"x": 0.54, "y": 0.035})
        self.defence_button.bind(on_press=lambda instance: self.choose("defence"))
        root.add_widget(self.defence_button)
        self.disable_buttons(True)

        self.network = NetworkClient(self)
        threading.Thread(target=self.network.connect, daemon=True).start()
        return root

    def update_background(self, instance, value):
        self.background.pos = instance.pos
        self.background.size = instance.size

    def disable_buttons(self, disabled):
        self.attack_button.disabled = disabled
        self.defence_button.disabled = disabled

    def network_error(self, text):
        self.status_label.text = "OFFLINE"
        self.message_label.text = "CONNECTION FAILED: " + text
        self.turn_label.text = ""
        self.disable_buttons(True)
        self.busy = True

    def update_counts(self, own, opponent):
        self.cards_label.text = f"YOU: {own}   OPPONENT: {opponent}"

    def set_turn(self, turn, your_turn):
        self.my_turn = your_turn
        if your_turn:
            self.turn_label.text = "YOUR TURN - CHOOSE A POWER"
            self.turn_label.color = (0.3, 1, 0.5, 1)
        else:
            self.turn_label.text = f"PLAYER {turn + 1} TURN - WAIT"
            self.turn_label.color = (1, 0.8, 0.3, 1)

    def handle_message(self, m):
        msg_type = m.get("type")
        if msg_type == "connected":
            self.player_number = m.get("player", 0)
            self.status_label.text = "PLAYER " + str(self.player_number + 1) + " CONNECTED"
            self.message_label.text = "WAITING FOR SECOND PLAYER"
            return
        if msg_type == "status":
            self.status_label.text = m.get("text", "ONLINE")
            return
        if msg_type == "game_start":
            self.player_number = m.get("player", 0)
            self.round_label.text = "ROUND 1"
            self.current_deck = m.get("deck", [])
            self.set_card(m["card"], m.get("cards_left", 16), m.get("opponent_cards", 16))
            self.status_label.text = "ONLINE - BATTLE READY"
            self.set_turn(m.get("turn", 0), m.get("your_turn", False))
            self.message_label.text = "CHOOSE ATTACK OR DEFENCE" if m.get("your_turn") else "WAIT FOR OPPONENT"
            self.busy = not m.get("your_turn", False)
            self.disable_buttons(not m.get("your_turn", False))
            return
        if msg_type == "choice_received":
            self.message_label.text = m.get("text", "YOUR CHOICE LOCKED - WAITING FOR OPPONENT")
            self.busy = True
            self.disable_buttons(True)
            return
        if msg_type == "not_your_turn":
            self.message_label.text = m.get("text", "WAIT FOR YOUR TURN")
            self.my_turn = False
            self.busy = True
            self.disable_buttons(True)
            return
        if msg_type == "opponent_choice":
            category = m.get("category", "").upper()
            self.message_label.text = "OPPONENT CHOSE " + category
            self.flash_message()
            return
        if msg_type == "turn_changed":
            self.my_turn = bool(m.get("your_turn", False))
            self.busy = not self.my_turn
            self.set_turn(m.get("turn", self.player_number), self.my_turn)
            if self.my_turn:
                self.message_label.text = "OPPONENT CHOSE - YOUR TURN"
                self.disable_buttons(False)
            else:
                self.message_label.text = m.get("text", "WAIT FOR OPPONENT")
                self.disable_buttons(True)
            return
        if msg_type == "round_result":
            self.show_round_result(m)
            return
        if msg_type == "next_round":
            self.round_label.text = "ROUND " + str(m["round"])
            self.current_deck = m.get("deck", [])
            self.set_card(m["card"], m.get("cards_left", 0), m.get("opponent_cards", 0))
            self.set_turn(m.get("turn", 0), m.get("your_turn", False))
            self.message_label.text = "YOUR TURN - CHOOSE" if m.get("your_turn") else f"PLAYER {m.get('turn', 0) + 1} CHOOSES"
            self.busy = not m.get("your_turn", False)
            self.disable_buttons(not m.get("your_turn", False))
            return
        if msg_type == "game_over":
            winner = m.get("winner", -1)
            text = "YOU WIN THE GAME!" if winner == self.player_number else "OPPONENT WINS THE GAME!"
            if self.player_number == 0:
                self.update_counts(m.get("cards0", 0), m.get("cards1", 0))
            else:
                self.update_counts(m.get("cards1", 0), m.get("cards0", 0))
            self.show_game_over(text)
            self.disable_buttons(True)
            self.busy = True

    def set_card(self, card, own_count, opponent_count):
        if self.card_widget and self.card_widget.parent:
            self.card_widget.parent.remove_widget(self.card_widget)
        self.card_widget = PlayerCard(card)
        self.root.add_widget(self.card_widget)
        self.update_counts(own_count, opponent_count)
        self.card_widget.opacity = 0
        self.card_widget.y -= 20
        Animation(opacity=1, y=self.card_widget.y + 20, duration=0.25, t="out_quad").start(self.card_widget)

    def choose(self, category):
        if self.busy or not self.my_turn or not self.network.running:
            return
        self.busy = True
        self.disable_buttons(True)
        self.message_label.text = "YOU CHOSE " + category.upper()
        self.flash_message()
        self.network.send({"type": "choice", "category": category})

    def flash_message(self):
        self.message_label.font_size = 22
        self.message_label.opacity = 0
        Animation(opacity=1, duration=0.12).start(self.message_label)
        Clock.schedule_once(lambda dt: setattr(self.message_label, "font_size", 15), 0.55)

    def battle_animation(self, winner):
        if not self.card_widget:
            return
        original_x = self.card_widget.x
        distance = 35 if winner == self.player_number else -35 if winner in (0, 1) else 0
        if distance:
            anim = Animation(x=original_x + distance, duration=0.10, t="out_quad")
            anim += Animation(x=original_x - distance * 0.55, duration=0.08)
            anim += Animation(x=original_x, duration=0.10)
            anim.start(self.card_widget)
        self.message_label.font_size = 24
        self.message_label.opacity = 0
        Animation(opacity=1, duration=0.12).start(self.message_label)
        Clock.schedule_once(lambda dt: setattr(self.message_label, "font_size", 15), 0.8)

    def show_round_result(self, m):
        winner = m.get("winner", -1)
        if winner == self.player_number:
            headline = "YOU WIN THIS ROUND!"
        elif winner == -1:
            headline = "DRAW - SAME TURN"
        else:
            headline = "OPPONENT WINS THIS ROUND!"

        if self.player_number == 0:
            your_choice, your_value = m["choice0"], m["value0"]
            opp_choice, opp_value = m["choice1"], m["value1"]
            your_cards, opp_cards = m["cards0"], m["cards1"]
        else:
            your_choice, your_value = m["choice1"], m["value1"]
            opp_choice, opp_value = m["choice0"], m["value0"]
            your_cards, opp_cards = m["cards1"], m["cards0"]

        self.update_counts(your_cards, opp_cards)
        self.message_label.text = headline
        self.battle_animation(winner)
        self.set_turn(m.get("next_turn", winner if winner >= 0 else 0), False)
        self.show_result_popup(headline, your_choice, your_value, opp_choice, opp_value, your_cards, opp_cards, m.get("next_turn", winner))

    def show_result_popup(self, headline, your_choice, your_value, opp_choice, opp_value, your_cards, opp_cards, next_turn):
        layout = BoxLayout(orientation="vertical", spacing=7, padding=12)
        layout.add_widget(Label(text=headline, font_size=21, bold=True, size_hint_y=0.18))
        layout.add_widget(Label(text=(
            f"YOU: {your_choice.upper()}  {your_value}\n"
            f"OPPONENT: {opp_choice.upper()}  {opp_value}\n\n"
            f"YOUR CARDS: {your_cards}\n"
            f"OPPONENT CARDS: {opp_cards}\n\n"
            f"NEXT TURN: PLAYER {next_turn + 1}"
        ), font_size=14, size_hint_y=0.58))
        button = Button(text="NEXT ROUND", font_size=16, bold=True, size_hint_y=0.20)
        layout.add_widget(button)
        popup = Popup(title="ROUND RESULT", content=layout, size_hint=(0.70, 0.55), auto_dismiss=False)
        button.bind(on_press=lambda instance: popup.dismiss())
        popup.open()

    def show_my_cards(self):
        if not self.current_deck:
            return
        scroll = ScrollView()
        box = BoxLayout(orientation="vertical", spacing=4, padding=8, size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        for index, card in enumerate(self.current_deck, 1):
            box.add_widget(Label(
                text=f"{index}. {str(card['name']).upper()}   A:{card['attack']}   D:{card['defence']}",
                font_size=13,
                size_hint_y=None,
                height=28,
            ))
        scroll.add_widget(box)
        popup = Popup(title=f"MY CARDS ({len(self.current_deck)})", content=scroll, size_hint=(0.88, 0.78))
        popup.open()

    def show_game_over(self, message):
        layout = BoxLayout(orientation="vertical", spacing=8, padding=15)
        layout.add_widget(Label(text=message, font_size=22, bold=True, size_hint_y=0.45))
        button = Button(text="CLOSE", font_size=16, bold=True, size_hint_y=0.25)
        layout.add_widget(button)
        popup = Popup(title="GAME OVER", content=layout, size_hint=(0.70, 0.40), auto_dismiss=False)
        button.bind(on_press=lambda instance: popup.dismiss())
        popup.open()

    def on_stop(self):
        self.network.close()


if __name__ == "__main__":
    OnlineAndroidGame().run()
