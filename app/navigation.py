"""Which pages each role sees, in one place.

app.py turns this into the menu (st.navigation). Each role gets ONLY its
own pages: a page that is not in a role's list cannot be opened by that
role, even by typing its address. Check this list whenever you add a page.
"""

# url path -> (menu title, Material icon)
PAGES = {
    "home": ("Home", ":material/home:"),
    "my-restaurant": ("My restaurant", ":material/storefront:"),
    "my-organization": ("My organization", ":material/apartment:"),
    "available-food": ("Available food", ":material/restaurant:"),
    "donations": ("Food donations", ":material/soup_kitchen:"),
    "pickups": ("Pickup requests", ":material/local_shipping:"),
    "restaurants": ("Restaurants", ":material/store:"),
    "organizations": ("Organizations", ":material/groups:"),
    "volunteers": ("Volunteers", ":material/directions_walk:"),
    "admin": ("Reports & tools", ":material/insights:"),
    "user-access": ("User access", ":material/manage_accounts:"),
}

# Titles that read better for one role.
TITLE_FOR_ROLE = {
    ("VOLUNTEER", "pickups"): "My pickups",
    ("DONOR", "donations"): "My donations",
}

# role -> menu sections -> pages (url paths). "" = no section heading.
MENU = {
    "ADMIN": {
        "": ["home"],
        "Food": ["donations", "pickups", "restaurants"],
        "People": ["organizations", "volunteers", "user-access"],
        "Ministry": ["admin"],
    },
    "DONOR": {"": ["home", "my-restaurant", "donations"]},
    "ORGANIZATION": {
        "": ["home", "my-organization", "available-food", "pickups"],
    },
    "VOLUNTEER": {"": ["home", "pickups"]},
}


def pages_for(role):
    """Flat list of the url paths a role may open."""
    return [path for paths in MENU.get(role, {}).values() for path in paths]


def title_for(role, path):
    return TITLE_FOR_ROLE.get((role, path), PAGES[path][0])
