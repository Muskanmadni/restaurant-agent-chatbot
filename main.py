import streamlit as st
import asyncio
import os
import re
import random
import string
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, OpenAIChatCompletionsModel, set_tracing_disabled

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "meta-llama/llama-3.2-1b-instruct:free"

client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=BASE_URL)
set_tracing_disabled(disabled=True)

async def generate_menu_via_agent(restaurant):
    agent = Agent(
        name="MenuBot",
        instructions=f"You are a helpful assistant generating restaurant menus. Create a short menu with 5-6 items for {restaurant}, using emojis and prices.",
        model=OpenAIChatCompletionsModel(model=MODEL, openai_client=client),
    )
    result = await Runner.run(agent, f"Give me the menu for {restaurant}")
    return result.final_output.strip()

def get_dynamic_menu(restaurant):
    return asyncio.run(generate_menu_via_agent(restaurant))

class RestaurantChatbot:
    def __init__(self, api_key, restaurant):
        self.api_key = api_key
        self.restaurant = restaurant

        self.menu = """
🍗 **Korean Menu**
1. **Korean Fried Chicken** - $12.99
2. **Bibimbap** - $10.99
3. **Tteokbokki** - $8.99
4. **Kimchi Fried Rice** - $9.99
5. **Korean BBQ Platter** - $15.99
6. **Banchan** - $5.99
7. **Korean Corn Cheese** - $6.99
8. **Hotteok** - $4.99
9. **Korean Spicy Noodles** - $7.99
10. **Sikhye** - $3.99

    **Dessert Menu**
11. **Bingsu** - $6.99
12. **Patbingsu** - $7.99
13. **Injeolmi Toast** - $5.99
14. **Sundae** - $4.99

       **Drinks**
15. **Korean Iced Tea** - $2.99
16. **Korean Lemonade** - $2.99
17. **Banana Milk** - $1.99

      **Sides**
18. **Kimchi** - $2.99
19. **Pickled Radish** - $1.99
20. **Spicy Cucumber Salad** - $3.99
21. **Seaweed Salad** - $4.99
22. **Fried Tofu** - $5.99
23. **Korean Pancakes** - $6.99
"""

        self.menu_items = {
            "korean fried chicken": 12.99,
            "bibimbap": 10.99,
            "tteokbokki": 8.99,
            "kimchi fried rice": 9.99,
            "korean bbq platter": 15.99,
            "banchan": 5.99,
            "korean corn cheese": 6.99,
            "hotteok": 4.99,
            "korean spicy noodles": 7.99,
            "sikhye": 3.99,
            "bingsu": 6.99,
            "patbingsu": 7.99,
            "injeolmi toast": 5.99,
            "sundae": 4.99,
            "korean iced tea": 2.99,
            "korean lemonade": 2.99,
            "banana milk": 1.99,
            "kimchi": 2.99,
            "pickled radish": 1.99,
            "spicy cucumber salad": 3.99,
            "seaweed salad": 4.99,
            "fried tofu": 5.99,
            "korean pancakes": 6.99,
        }

        if "history" not in st.session_state or st.session_state.history is None:
            st.session_state.history = []
        for key in ["orders", "delivery_type", "address", "contact", "payment_method", "tracking_number", "delivery_estimate"]:
            if key not in st.session_state:
                st.session_state[key] = None
        if "step" not in st.session_state:
            st.session_state.step = "init"

    def calculate_order_summary(self):
        items = st.session_state.orders.lower()
        order_lines = []
        total = 0.0

        for name, price in self.menu_items.items():
            pattern = rf"(\d+)?\s*{re.escape(name)}"
            match = re.search(pattern, items)
            if match:
                qty = int(match.group(1)) if match.group(1) else 1
                subtotal = qty * price
                order_lines.append(f"{qty} x {name.title()} - ${subtotal:.2f}")
                total += subtotal

        return order_lines, total

    def summarize_order(self):
        order_lines, total = self.calculate_order_summary()
        item_summary = "\n".join([f"- 🛒 {line}" for line in order_lines]) if order_lines else "No valid items found."

        summary = f"""🧾 **Order Summary**
{item_summary}
- 💵 **Total**: ${total:.2f}
- 🚚 Type: {st.session_state.delivery_type}
"""
        if st.session_state.delivery_type == "Delivery":
            summary += f"- 📍 Address: {st.session_state.address}\n"
        summary += f"""- ☎️ Contact: {st.session_state.contact}
- 💳 Payment: {st.session_state.payment_method}

👉 Type **confirm** to place your order.
"""
        return summary

    def process_user_input(self, user_input):
        user_input_lower = user_input.lower().strip()

        # 🔍 Track order by tracking number
        if user_input_lower.startswith("track "):
            code = user_input.strip().split()[-1].upper()
            if st.session_state.tracking_number and code == st.session_state.tracking_number:
                status = random.choice(["Preparing your meal 🍳", "Out for delivery 🚗", "Delivered ✅"])
                return f"📦 Status for **{code}**: {status}"
            else:
                return "❌ Invalid or unknown tracking number. Please check and try again."

        # Chat flow
        if st.session_state.step == "init":
            if "menu" in user_input_lower:
                return f"Here is the menu for {self.restaurant}:\n{self.menu}"
            elif "order" in user_input_lower:
                st.session_state.step = "order_items"
                return "Great! What would you like to order?"
            else:
                return "You can say 'Show me the menu' or 'I want to order'."

        elif st.session_state.step == "order_items":
            st.session_state.orders = user_input
            st.session_state.step = "delivery_type"
            return "Would you like **Delivery** or **Pickup**?"

        elif st.session_state.step == "delivery_type":
            st.session_state.delivery_type = user_input.title()
            if "delivery" in user_input_lower:
                st.session_state.step = "address"
                return "Please provide your delivery address."
            else:
                st.session_state.step = "contact"
                return "Please provide your contact number."

        elif st.session_state.step == "address":
            st.session_state.address = user_input
            st.session_state.step = "contact"
            return "Please provide your contact number."

        elif st.session_state.step == "contact":
            st.session_state.contact = user_input
            st.session_state.step = "payment_method"
            return "Choose payment method: **Card** or **Cash on Delivery**"

        elif st.session_state.step == "payment_method":
            st.session_state.payment_method = user_input.title()
            st.session_state.step = "confirm"
            return self.summarize_order()

        elif st.session_state.step == "confirm":
            if "confirm" in user_input_lower or "yes" in user_input_lower:
                st.session_state.step = "done"
                tracking_number = "ORD-" + ''.join(random.choices(string.digits, k=6))
                st.session_state.tracking_number = tracking_number
                delivery_estimate = random.choice(["25–35 minutes", "30–45 minutes", "40–55 minutes"])
                st.session_state.delivery_estimate = delivery_estimate
                return f"""✅ **Order confirmed!** Thank you for ordering with us. 🎉

📦 Tracking number: **{tracking_number}**  
⏰ Estimated delivery: **{delivery_estimate}**

You can check your order status by typing:  
`track {tracking_number}`
"""
            else:
                return "Order cancelled. You can restart by saying 'I want to order'."

        elif st.session_state.step == "done":
            return f"""✅ You've already placed an order.

📦 Tracking number: **{st.session_state.tracking_number}**  
⏰ Estimated delivery: **{st.session_state.delivery_estimate}**

Type `track {st.session_state.tracking_number}` to check status.
Type 'I want to order' to place another.
"""

        return "I'm not sure what you mean. Try saying 'menu' or 'I want to order'."

    def chat(self, user_input):
        response = self.process_user_input(user_input)
        st.session_state.history.append(("You", user_input))
        st.session_state.history.append(("Bot", response))

    def display_chat(self):
        for sender, message in st.session_state.history:
            if sender == "You":
                st.markdown(
                    f"<div style='text-align:right; background:#d1e7dd; padding:10px; color:black; border-radius:10px; margin:5px 0; max-width:70%; margin-left:auto;'>"
                    f"<b>{sender}:</b><br>{message}</div>", unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='text-align:left; background:#f0f0f0; padding:10px;  color:black; border-radius:10px; margin:5px 0; max-width:70%; margin-right:auto;'>"
                    f"<b>{sender}:</b><br>{message}</div>", unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="🍱 Korean Restaurant Chatbot", layout="centered")

    st.markdown("""
    <style>
    .stApp {
        background-image: url('https://img.freepik.com/premium-photo/korean-food-cabbage-kimchi-black-dish-set-dark-background_38038-226.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🤖 Welcome to Korean Restaurant Chatbot!")

    st.markdown("""
    <div style='background-color: #1e3a8a; padding: 20px; border-radius: 12px; color: white;'>
        <h3>💡 Steps:</h3>
        <ol style="line-height: 1.8;">
            <li>Say: <b>Show me the menu</b></li>
            <li>Say: <b>I want to order</b></li>
            <li>Add your items (e.g. <i>2 bibimbap, 1 banana milk</i>)</li>
            <li>Choose: <b>Delivery</b> or <b>Pickup</b></li>
            <li>Provide: <b>Address & Contact Number</b></li>
            <li>Choose: <b>Card</b> or <b>Cash on Delivery</b></li>
            <li>Type: <b>confirm</b> to place the order ✅</li>
            <li>Type: <b>track ORD-XXXXXX</b> to check status</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    restaurant = "Korean"
    bot = RestaurantChatbot(OPENROUTER_API_KEY, restaurant)
    bot.display_chat()

    def on_send():
        if st.session_state.input.strip():
            bot.chat(st.session_state.input.strip())
            st.session_state.input = ""

    st.text_input("💬 Your message:", key="input")
    st.button("📤 Send", on_click=on_send)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([0.8, 0.2])
    with col2:
        if st.button("🔄 Reset Chat"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
