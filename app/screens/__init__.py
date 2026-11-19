"""One file per group of pages. app.py builds the menu and calls them.

Every page function takes a PageContext: who is signed in, their own
restaurant or organization (if any), and the other pages (for links).
Which role may open which page is decided in app/navigation.py; pages
that several roles share check `ctx.role` for what each one may DO.

    kitchens.py       My restaurant (donor), Restaurants (admin)
    organizations.py  My organization, Organizations (verify/reject)
    food.py           Food donations / My donations, Available food
    pickups.py        Pickup requests / My pickups
    people.py         Volunteers, User access
    reports.py        Reports & tools
"""

from dataclasses import dataclass, field


@dataclass
class PageContext:
    user: dict
    my_restaurant: tuple = None
    my_organization: tuple = None
    pages: dict = field(default_factory=dict)  # url path -> st.Page

    @property
    def role(self):
        return self.user["role"]

    @property
    def is_admin(self):
        return self.role == "ADMIN"
