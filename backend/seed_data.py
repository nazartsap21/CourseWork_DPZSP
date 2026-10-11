"""Static demo data for seed.py. Prices here are in whole UAH for readability;
seed.py converts them to kopiyky."""

from typing import TypedDict

DEMO_PASSWORD = "forkful123"

CUISINES = [
    "Ukrainian",
    "Italian",
    "Japanese",
    "Georgian",
    "American",
    "Vietnamese",
    "Middle Eastern",
    "Vegetarian",
]


class UserSeed(TypedDict):
    email: str
    name: str
    phone: str
    role: str


USERS: list[UserSeed] = [
    {
        "email": "admin@example.com",
        "name": "Iryna Savchuk",
        "phone": "+380671112233",
        "role": "admin",
    },
    {
        "email": "taras.courier@example.com",
        "name": "Taras Melnyk",
        "phone": "+380632224455",
        "role": "courier",
    },
    {
        "email": "andrii.courier@example.com",
        "name": "Andrii Koval",
        "phone": "+380503336677",
        "role": "courier",
    },
    {
        "email": "olena@example.com",
        "name": "Olena Hnatyshyn",
        "phone": "+380974448899",
        "role": "customer",
    },
    {
        "email": "maksym@example.com",
        "name": "Maksym Bondar",
        "phone": "+380935550011",
        "role": "customer",
    },
]


class DishSeed(TypedDict):
    name: str
    category: str
    price_uah: int
    description: str


class RestaurantSeed(TypedDict):
    name: str
    cuisines: list[str]
    description: str
    address: str
    lat: float
    lng: float
    avg_prep_minutes: int
    min_order_uah: int
    dishes: list[DishSeed]


def dish(name: str, category: str, price_uah: int, description: str) -> DishSeed:
    return {"name": name, "category": category, "price_uah": price_uah, "description": description}


RESTAURANTS: list[RestaurantSeed] = [
    {
        "name": "Khata Kozaka",
        "cuisines": ["Ukrainian"],
        "description": "Home-style Galician cooking a few steps from Rynok Square.",
        "address": "pl. Rynok 14, Lviv",
        "lat": 49.8418,
        "lng": 24.0313,
        "avg_prep_minutes": 25,
        "min_order_uah": 200,
        "dishes": [
            dish(
                "Red borshch with pampushky",
                "Soups",
                145,
                "Beetroot borshch, sour cream, garlic buns.",
            ),
            dish("Mushroom yushka", "Soups", 125, "Clear forest-mushroom soup with dill."),
            dish(
                "Varenyky with potato",
                "Mains",
                135,
                "Ten dumplings with fried onion and sour cream.",
            ),
            dish("Deruny with sour cream", "Mains", 140, "Crispy potato pancakes, three pieces."),
            dish(
                "Chicken Kyiv",
                "Mains",
                235,
                "Breaded chicken breast with herb butter, mashed potatoes.",
            ),
            dish("Holubtsi", "Mains", 195, "Cabbage rolls with pork and rice in tomato sauce."),
            dish(
                "Banosh with brynza",
                "Mains",
                175,
                "Cornmeal porridge, sheep cheese, crispy pork cracklings.",
            ),
            dish(
                "Lviv syrnyk", "Desserts", 115, "Baked cheesecake with raisins and chocolate glaze."
            ),
            dish("Uzvar", "Drinks", 55, "Dried fruit compote, 0.4 l."),
            dish("Kvass", "Drinks", 60, "House-brewed bread kvass, 0.5 l."),
        ],
    },
    {
        "name": "Varenyky Lychakiv",
        "cuisines": ["Ukrainian", "Vegetarian"],
        "description": "Hand-pinched varenyky, sweet and savoury, made every morning.",
        "address": "vul. Lychakivska 20, Lviv",
        "lat": 49.8409,
        "lng": 24.0428,
        "avg_prep_minutes": 20,
        "min_order_uah": 150,
        "dishes": [
            dish(
                "Varenyky with cherries",
                "Sweet varenyky",
                145,
                "Sour cherries, sugar, sour cream on the side.",
            ),
            dish(
                "Varenyky with cottage cheese",
                "Sweet varenyky",
                130,
                "Sweet cottage cheese and vanilla.",
            ),
            dish(
                "Varenyky with blueberries",
                "Sweet varenyky",
                155,
                "Carpathian blueberries, honey drizzle.",
            ),
            dish(
                "Varenyky with potato and mushrooms",
                "Savoury varenyky",
                135,
                "Mashed potato with fried porcini.",
            ),
            dish(
                "Varenyky with cabbage", "Savoury varenyky", 120, "Braised sauerkraut and carrot."
            ),
            dish(
                "Varenyky with brynza and greens",
                "Savoury varenyky",
                140,
                "Sheep cheese, dill and green onion.",
            ),
            dish(
                "Pelmeni with pork and beef", "Savoury varenyky", 160, "Fifteen pieces with butter."
            ),
            dish("Beetroot salad with walnuts", "Salads", 95, "Roasted beetroot, prunes, walnuts."),
            dish("Berry kysil", "Drinks", 50, "Warm berry drink, 0.3 l."),
        ],
    },
    {
        "name": "Forno Virmenska",
        "cuisines": ["Italian"],
        "description": "Neapolitan pizza from a wood-fired oven on Virmenska street.",
        "address": "vul. Virmenska 18, Lviv",
        "lat": 49.8434,
        "lng": 24.0322,
        "avg_prep_minutes": 20,
        "min_order_uah": 250,
        "dishes": [
            dish("Margherita", "Pizza", 215, "San Marzano tomatoes, fior di latte, basil."),
            dish("Diavola", "Pizza", 265, "Spicy salami, mozzarella, chili oil."),
            dish("Quattro formaggi", "Pizza", 285, "Mozzarella, gorgonzola, parmesan, brynza."),
            dish("Prosciutto e funghi", "Pizza", 275, "Cooked ham, champignons, mozzarella."),
            dish("Marinara", "Pizza", 175, "Tomato, garlic, oregano. No cheese."),
            dish("Calzone", "Pizza", 255, "Folded pizza with ricotta, ham and mushrooms."),
            dish("Burrata with tomatoes", "Starters", 245, "Burrata, cherry tomatoes, pesto."),
            dish("Focaccia", "Starters", 85, "Rosemary and sea salt."),
            dish("Tiramisu", "Desserts", 135, "Mascarpone, savoiardi, espresso."),
            dish("San Pellegrino", "Drinks", 75, "Sparkling water, 0.5 l."),
            dish("Lemonade", "Drinks", 80, "Lemon and mint, 0.4 l."),
        ],
    },
    {
        "name": "Trattoria Kopernyka",
        "cuisines": ["Italian"],
        "description": "Fresh pasta and slow-cooked sauces, family recipes from Emilia.",
        "address": "vul. Kopernyka 9, Lviv",
        "lat": 49.8376,
        "lng": 24.0257,
        "avg_prep_minutes": 30,
        "min_order_uah": 300,
        "dishes": [
            dish(
                "Tagliatelle al ragu", "Pasta", 255, "Egg pasta with six-hour beef and pork ragu."
            ),
            dish(
                "Spaghetti carbonara", "Pasta", 245, "Guanciale, egg yolk, pecorino, black pepper."
            ),
            dish("Penne arrabbiata", "Pasta", 195, "Spicy tomato sauce with garlic."),
            dish("Tortellini in brodo", "Pasta", 235, "Meat tortellini in capon broth."),
            dish("Mushroom risotto", "Mains", 265, "Carnaroli rice, porcini, parmesan."),
            dish("Lasagna bolognese", "Mains", 275, "Layered with ragu and bechamel."),
            dish("Caesar salad", "Salads", 205, "Romaine, chicken, croutons, anchovy dressing."),
            dish("Minestrone", "Soups", 145, "Seasonal vegetables and beans."),
            dish("Panna cotta", "Desserts", 125, "Vanilla cream with berry coulis."),
            dish("Espresso tonic", "Drinks", 90, "Espresso over tonic and ice."),
        ],
    },
    {
        "name": "Sora Ramen",
        "cuisines": ["Japanese"],
        "description": "Rich broths simmered for twelve hours, noodles made in-house.",
        "address": "vul. Doroshenka 21, Lviv",
        "lat": 49.8401,
        "lng": 24.0222,
        "avg_prep_minutes": 20,
        "min_order_uah": 200,
        "dishes": [
            dish("Tonkotsu ramen", "Ramen", 285, "Pork bone broth, chashu, ajitama egg, nori."),
            dish("Shoyu ramen", "Ramen", 265, "Soy chicken broth, chashu, bamboo shoots."),
            dish("Miso ramen", "Ramen", 275, "Miso broth, minced pork, corn, butter."),
            dish("Vegan tantanmen", "Ramen", 255, "Sesame-chili soy broth, tofu, bok choy."),
            dish("Gyoza with pork", "Starters", 155, "Six pan-fried dumplings, ponzu."),
            dish("Edamame", "Starters", 95, "Steamed with sea salt."),
            dish("Karaage", "Starters", 175, "Japanese fried chicken, kewpie mayo."),
            dish("Chashu don", "Rice", 215, "Rice bowl with braised pork belly."),
            dish("Matcha cheesecake", "Desserts", 135, "Baked cheesecake with matcha."),
            dish("Ramune", "Drinks", 95, "Japanese lemonade, 0.2 l."),
        ],
    },
    {
        "name": "Hachi Sushi Bar",
        "cuisines": ["Japanese"],
        "description": "Rolls and nigiri prepared to order on Svobody avenue.",
        "address": "prosp. Svobody 27, Lviv",
        "lat": 49.8433,
        "lng": 24.0264,
        "avg_prep_minutes": 35,
        "min_order_uah": 400,
        "dishes": [
            dish("Philadelphia roll", "Rolls", 345, "Salmon, cream cheese, cucumber. 8 pcs."),
            dish("California roll", "Rolls", 295, "Crab, avocado, cucumber, tobiko. 8 pcs."),
            dish("Dragon roll", "Rolls", 385, "Eel, avocado, unagi sauce. 8 pcs."),
            dish("Spicy tuna roll", "Rolls", 325, "Tuna, spicy mayo, green onion. 8 pcs."),
            dish("Kappa maki", "Rolls", 125, "Cucumber and sesame. 6 pcs."),
            dish("Salmon nigiri", "Nigiri", 165, "Two pieces."),
            dish("Eel nigiri", "Nigiri", 185, "Two pieces with unagi sauce."),
            dish("Salmon sashimi", "Sashimi", 295, "Eight slices."),
            dish("Miso soup", "Soups", 85, "Tofu, wakame, green onion."),
            dish("Seaweed salad", "Salads", 135, "Chuka wakame with sesame."),
            dish(
                "Set Hachi",
                "Sets",
                1150,
                "Philadelphia, California, Dragon and Kappa maki. 30 pcs.",
            ),
            dish("Green tea", "Drinks", 60, "Sencha, 0.5 l pot."),
        ],
    },
    {
        "name": "Supra Courtyard",
        "cuisines": ["Georgian"],
        "description": "Khachapuri, khinkali and grilled meats in an old-town courtyard.",
        "address": "vul. Staroievreiska 4, Lviv",
        "lat": 49.8406,
        "lng": 24.0333,
        "avg_prep_minutes": 30,
        "min_order_uah": 250,
        "dishes": [
            dish(
                "Khachapuri Adjaruli",
                "Khachapuri",
                245,
                "Boat-shaped bread with cheese, egg and butter.",
            ),
            dish("Khachapuri Imeruli", "Khachapuri", 225, "Round pie filled with suluguni."),
            dish(
                "Khinkali with beef and pork", "Khinkali", 38, "One dumpling; order five or more."
            ),
            dish(
                "Khinkali with mushrooms",
                "Khinkali",
                34,
                "One dumpling with champignons and herbs.",
            ),
            dish("Pork mtsvadi", "Grill", 295, "Skewered pork neck with onion and pomegranate."),
            dish("Chicken chkmeruli", "Mains", 315, "Chicken baked in garlic cream sauce."),
            dish("Lobio", "Mains", 155, "Red beans stewed with coriander and walnuts."),
            dish("Pkhali assortment", "Starters", 185, "Spinach, beetroot and leek walnut pates."),
            dish("Badrijani", "Starters", 175, "Aubergine rolls with walnut paste."),
            dish("Tarkhun lemonade", "Drinks", 70, "Tarragon soda, 0.5 l."),
        ],
    },
    {
        "name": "Smokehouse Hnatiuka",
        "cuisines": ["American"],
        "description": "Smashed burgers and low-and-slow barbecue.",
        "address": "vul. Hnatiuka 10, Lviv",
        "lat": 49.8398,
        "lng": 24.0281,
        "avg_prep_minutes": 20,
        "min_order_uah": 200,
        "dishes": [
            dish(
                "Classic smash burger",
                "Burgers",
                235,
                "Two beef patties, cheddar, pickles, house sauce.",
            ),
            dish("Bacon BBQ burger", "Burgers", 275, "Beef, bacon, onion rings, BBQ sauce."),
            dish("Crispy chicken burger", "Burgers", 225, "Fried chicken thigh, slaw, spicy mayo."),
            dish("Mushroom burger", "Burgers", 215, "Portobello, brynza, caramelised onion."),
            dish(
                "Pulled pork sandwich", "Barbecue", 245, "Twelve-hour smoked pork shoulder, slaw."
            ),
            dish("Smoked pork ribs", "Barbecue", 395, "Half rack with BBQ glaze."),
            dish("Buffalo wings", "Sides", 195, "Eight wings, blue cheese dip."),
            dish("Fries", "Sides", 85, "Skin-on, sea salt."),
            dish("Mac and cheese", "Sides", 125, "Baked with cheddar crust."),
            dish("Brownie", "Desserts", 95, "Dark chocolate, walnuts."),
            dish("Craft cola", "Drinks", 65, "0.33 l."),
        ],
    },
    {
        "name": "Pho Horodotska",
        "cuisines": ["Vietnamese"],
        "description": "Pho and banh mi made the way they are in Hanoi.",
        "address": "vul. Horodotska 45, Lviv",
        "lat": 49.8431,
        "lng": 24.0089,
        "avg_prep_minutes": 15,
        "min_order_uah": 150,
        "dishes": [
            dish("Pho bo", "Pho", 215, "Beef broth, rice noodles, sliced beef, herbs."),
            dish("Pho ga", "Pho", 195, "Chicken broth, rice noodles, chicken."),
            dish("Bun bo Hue", "Noodles", 225, "Spicy lemongrass beef noodle soup."),
            dish("Bun cha", "Noodles", 235, "Grilled pork, rice noodles, dipping sauce."),
            dish("Banh mi with pork", "Banh mi", 165, "Baguette, pork, pate, pickled vegetables."),
            dish("Banh mi with tofu", "Banh mi", 145, "Baguette, crispy tofu, herbs."),
            dish("Fresh spring rolls", "Starters", 145, "Shrimp, rice paper, peanut sauce. 4 pcs."),
            dish("Fried nem rolls", "Starters", 135, "Pork and glass noodles. 4 pcs."),
            dish("Vietnamese iced coffee", "Drinks", 85, "Strong coffee with condensed milk."),
        ],
    },
    {
        "name": "Levant Kitchen",
        "cuisines": ["Middle Eastern", "Vegetarian"],
        "description": "Hummus, falafel and charcoal-grilled kebabs near Franka street.",
        "address": "vul. Ivana Franka 25, Lviv",
        "lat": 49.8352,
        "lng": 24.0372,
        "avg_prep_minutes": 20,
        "min_order_uah": 180,
        "dishes": [
            dish("Classic hummus", "Mezze", 135, "Tahini, olive oil, warm pita."),
            dish("Hummus with lamb", "Mezze", 215, "Topped with spiced minced lamb and pine nuts."),
            dish("Baba ganoush", "Mezze", 145, "Smoked aubergine, tahini, pomegranate."),
            dish("Falafel plate", "Mains", 195, "Six falafel, salad, tahini sauce."),
            dish("Chicken shawarma", "Mains", 185, "In lavash with garlic sauce and pickles."),
            dish("Lamb kofta", "Grill", 285, "Two skewers with bulgur and yogurt sauce."),
            dish("Shakshuka", "Mains", 165, "Eggs baked in spiced tomato sauce."),
            dish("Tabbouleh", "Salads", 125, "Parsley, bulgur, tomato, lemon."),
            dish("Baklava", "Desserts", 95, "Pistachio, three pieces."),
            dish("Ayran", "Drinks", 55, "Salted yogurt drink, 0.3 l."),
        ],
    },
]


class OrderSeed(TypedDict, total=False):
    customer: str
    restaurant: str
    items: list[tuple[str, int]]
    delivery_method: str
    payment_method: str
    status: str
    days_ago: int
    courier: str
    address: str
    lat: float
    lng: float
    free_delivery: bool
    regular_discount: bool
    bonus_points_used: int
    review: tuple[int, str]


OLENA_HOME = {"address": "vul. Kniazia Romana 12, apt 7", "lat": 49.8379, "lng": 24.0347}
MAKSYM_HOME = {"address": "vul. Zelena 48, apt 21", "lat": 49.8300, "lng": 24.0520}

# Olena reaches the regular-customer threshold (5 orders) and bought the
# premium card 12 days ago, so her recent orders have free delivery.
ORDERS: list[OrderSeed] = [
    {
        "customer": "olena@example.com",
        "restaurant": "Forno Virmenska",
        "items": [("Margherita", 1), ("Diavola", 1), ("Lemonade", 2)],
        "delivery_method": "standard",
        "payment_method": "mock",
        "status": "delivered",
        "days_ago": 48,
        "courier": "taras.courier@example.com",
        **OLENA_HOME,
        "review": (5, "Pizza arrived hot, the crust was still crisp."),
    },
    {
        "customer": "olena@example.com",
        "restaurant": "Sora Ramen",
        "items": [("Tonkotsu ramen", 2), ("Gyoza with pork", 1)],
        "delivery_method": "express",
        "payment_method": "cash",
        "status": "delivered",
        "days_ago": 37,
        "courier": "andrii.courier@example.com",
        **OLENA_HOME,
        "review": (4, "Great broth. Noodles a bit soft after the ride."),
    },
    {
        "customer": "olena@example.com",
        "restaurant": "Khata Kozaka",
        "items": [("Red borshch with pampushky", 2), ("Varenyky with potato", 1), ("Uzvar", 2)],
        "delivery_method": "standard",
        "payment_method": "mock",
        "status": "delivered",
        "days_ago": 29,
        "courier": "taras.courier@example.com",
        **OLENA_HOME,
    },
    {
        "customer": "olena@example.com",
        "restaurant": "Levant Kitchen",
        "items": [("Falafel plate", 1), ("Classic hummus", 1), ("Baklava", 2)],
        "delivery_method": "pickup",
        "payment_method": "cash",
        "status": "delivered",
        "days_ago": 21,
        "review": (5, "Best falafel in Lviv, ready exactly on time."),
    },
    {
        "customer": "olena@example.com",
        "restaurant": "Forno Virmenska",
        "items": [("Quattro formaggi", 1), ("Tiramisu", 1)],
        "delivery_method": "standard",
        "payment_method": "mock",
        "status": "delivered",
        "days_ago": 10,
        "courier": "andrii.courier@example.com",
        **OLENA_HOME,
        "free_delivery": True,
        "bonus_points_used": 20,
    },
    {
        "customer": "olena@example.com",
        "restaurant": "Supra Courtyard",
        "items": [
            ("Khachapuri Adjaruli", 1),
            ("Khinkali with beef and pork", 6),
            ("Tarkhun lemonade", 1),
        ],
        "delivery_method": "express",
        "payment_method": "mock",
        "status": "delivered",
        "days_ago": 3,
        "courier": "taras.courier@example.com",
        **OLENA_HOME,
        "free_delivery": True,
        "regular_discount": True,
        "review": (5, "Khinkali were perfect. Courier called ahead."),
    },
    {
        "customer": "maksym@example.com",
        "restaurant": "Smokehouse Hnatiuka",
        "items": [("Classic smash burger", 2), ("Fries", 2), ("Craft cola", 2)],
        "delivery_method": "standard",
        "payment_method": "cash",
        "status": "delivered",
        "days_ago": 15,
        "courier": "andrii.courier@example.com",
        **MAKSYM_HOME,
        "review": (4, "Solid burgers, fries could be crispier."),
    },
    {
        "customer": "maksym@example.com",
        "restaurant": "Hachi Sushi Bar",
        "items": [("Set Hachi", 1), ("Miso soup", 2)],
        "delivery_method": "standard",
        "payment_method": "mock",
        "status": "cancelled",
        "days_ago": 8,
        **MAKSYM_HOME,
    },
    {
        "customer": "maksym@example.com",
        "restaurant": "Pho Horodotska",
        "items": [("Pho bo", 1), ("Banh mi with pork", 1), ("Vietnamese iced coffee", 1)],
        "delivery_method": "express",
        "payment_method": "mock",
        "status": "delivered",
        "days_ago": 5,
        "courier": "taras.courier@example.com",
        **MAKSYM_HOME,
    },
]

FAVORITES = {
    "olena@example.com": ["Forno Virmenska", "Supra Courtyard", "Levant Kitchen"],
    "maksym@example.com": ["Smokehouse Hnatiuka"],
}

PREMIUM_CARD = {"customer": "olena@example.com", "bought_days_ago": 12}
