import pickle
import random
import time
import matplotlib
import csv
import traceback

import matplotlib.pyplot as plt
from drink import Drink
from pytimedinput import timedInput


# TODO: Prijs verhoging statiegeld 10 cent

matplotlib.use("TkAgg")

plt.ion()

balance = 0
inventory = {}
time_stamps = [time.time()]
timeout = 10
min_balance = -5000
max_balance = 500


def initialise_inventory():
    """
    This will later be changed to read input from a csv file to improve usability
    """

    with open("inventaris.txt", "r") as f:
        bestand = csv.DictReader(f, delimiter="\t")
        for i, bier in enumerate(bestand):
            inventory[i] = Drink(
                bier["naam"],
                i,
                int(bier["min_prijs"]),
                int(bier["max_prijs"]),
                int(bier["per_prijs"]),
                int(bier["totaal stuks"]),
            )


def print_valid_stock() -> None:
    for value in inventory.values():
        print(value)


def update_prices(drink: Drink, amount: int, balance):
    """
    Updates all prices of the drinks based on the latest sale.
    Parameter drink (Drink) is the drink that is sold, hence its price increases.
    All other prices must decrease, as they are not sold in the latest transaction
    """
    if drink == None:
        for value in inventory.values():
            fraction_left = value.nr_drinks / value.initial_nr_drinks  # percentage of original nr of drinks
            volatility = 1 + (1 - fraction_left) /2
            price_change = random.gauss(3, 8 ** volatility)

            # extra compensation for out of bounds balance
            if balance > max_balance and value.historic_prices[-1] > 0.8 * value.starting_price:
                value.modify_price(False, price_change, 0)
            elif balance < min_balance and value.historic_prices[-1] < 1.2*value.starting_price:
                value.modify_price(True, price_change, 0)
            else:
                neg_or_pos = random.uniform(0, 1)
                if neg_or_pos < 0.8:
                    value.modify_price(False, price_change, 0)
                else: 
                    value.modify_price(False, -price_change, 0)
    else:
        for value in inventory.values():
            if value == drink:
                price_change = random.gauss(
                    (amount**1.2) * 10, (amount**1.2) * 3
                )
            else:
                price_change = random.gauss(
                    10, 3
                )

            # extra compensation for out of bounds balance
            if balance > max_balance and value != drink:
                value.modify_price(False, price_change, 0)
            elif balance < min_balance and value != drink:
                value.modify_price(True, price_change, 0)
            elif value == drink:
                value.modify_price(True, price_change, amount)
            else:
                value.modify_price(False, price_change, 0)


def sell_drink(drink: Drink, amount: int, balance):
    """
    Function used to sell a drink. Used to show the sell price to
    the user (i.e. how much somebody needs to pay for their order),
    and updates the borrel balance
    """
    time_stamps.append(time.time())
    sell_price = (drink.current_price * amount) / 100
    profit = (drink.current_price - drink.starting_price) * amount
    balance += profit
    print(f"\nSold for €{drink.current_price/100:.2f} per bottle")
    print(f"Sell price is €{sell_price:.2f}")
    print(f"Current balance is: €{balance/100:.2f}")
    if balance < min_balance:
        print("Past lower bound of balance, extra increase to prices")
    if balance > max_balance:
        print("Past upper bound of balance, extra decrease to prices")

    print("\n --------------------------- \n")
    return balance


def reset() -> None:
    """
    Resets all drink prices in the inventory to their default value,
    which is stored in the Drink object associated with the drink
    """
    for value in inventory.values():
        value.reset()


def quit() -> None:
    """
    Used to properly shutdown the borrel at the end. Useful to determine how much of each drink has been sold.
    """
    with open("finalInventory.pkl", "wb") as f:
        pickle.dump(inventory, f)
    print("Final results of drinks sold written to file")
    plt.close("all")


def safe_id_parse(prompt: str):
    """
    Used to make sure that we can properly parse inputs to integers.
    Additionally, performs checks for other possible commands and calls
    the functions associated with these commands when needed.
    Returns the parsed result when appropiate, along with a flag that indicates
    whether the program needs to continue running.
    """
    result, timedOut = timedInput(prompt, timeout=5)
    while result.isdigit() == False and not timedOut:
        print("Input must be an integer \n")
        result, timedOut = timedInput(prompt, timeout=5)
    if timedOut:
        return None, True, timedOut
    else:
        if result == "quit":
            return quit(), False, timedOut
        if result == "crash":
            return "crash", True, timedOut
        if result == "reset":
            return "reset", True, timedOut

        return int(result), True, timedOut


def safe_parse(prompt: str):
    """
    Used to make sure that we can properly parse inputs to integers.
    Additionally, performs checks for other possible commands and calls
    the functions associated with these commands when needed.
    Returns the parsed result when appropiate, along with a flag that indicates
    whether the program needs to continue running.
    """
    result = input(prompt)
    if result == "quit":
        return quit(), False
    if result == "crash":
        return "crash", True
    if result == "reset":
        return "reset", True
    while result.isdigit() == False:
        print("Input must be an integer \n")
        result = input(prompt)
    return int(result), True


"""
Main control loop that takes care of running the borrel. 
"""
initialise_inventory()
# Keep track of a boolean flag that indicates when the program should be terminated
running = True

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(1, 1, 1)
plots = []
for i, drank in enumerate(inventory.values()):
    (lines,) = ax.plot([], [])
    plots.append(lines)
ax.set_ylim(0, 350)
for line in plots:
    line.set_linewidth(4)
plt.xlabel("Time")
plt.ylabel("Price in cents")
print(plt.isinteractive())
plt.subplots_adjust(left=0.2)
plt.show()

try:
    while running:
        print_valid_stock()
        id, running, timedOut = safe_id_parse("ID of the drink sold: >> ")
        if not timedOut:

            if running == False:
                break

            # Continue until a valid ID is entered. ID entered must be associated with a drink
            while id not in inventory:
                print("That input is not valid, please use a valid ID")
                print_valid_stock()
                id, running, timedOut = safe_id_parse("ID of the drink sold: >> ")
                if running == False:
                    break
            drink = inventory[id]

            amount, running = safe_parse("Number of drinks sold: >> ")
            if amount == "crash":
                drink.crash_price()
                print(f"Crashed price of {drink.name} \n")
                continue
            if amount == "reset":
                drink.reset()
                print(f"reset price of {drink.name} \n")
                continue
            if running == False:
                break

            # Continue until user enters a valid amount of drinks to be ordered
            while (
                drink.can_sell_amount(amount) == False
            ):  # is possible to sell 0 drinks
                print("You can not sell this amount of drinks")
                print(f"You can sell at most {drink.nr_drinks} bottles")
                amount, running = safe_parse("Number of drinks sold: >> ")
                if amount == "crash":
                    drink.crash_price()
                    print(f"Crashed price of {drink.name} \n")
                    print_valid_stock()
                    continue
                if amount == "reset":
                    drink.reset()
                    print(f"reset price of {drink.name} \n")
                    print_valid_stock()
                    continue
                if running == False:
                    break

            balance = sell_drink(drink, amount, balance)

            update_prices(drink, amount, balance)
            print_valid_stock()
        else:
            update_prices(None, 0, balance)
            print("Updating prices due to timeout...\n")
            time_stamps.append(time.time())

        for i, drink in enumerate(
            inventory.values()
        ):  # TODO: sold out drinks do not appear on graph
            if not drink.for_sale:
                label = f"{drink.name} :: SOLD OUT"
                drink.historic_prices[-1] = 10000
            else:
                label = f"{drink.name} :: (€{drink.current_price/100:.2f})"
            plots[i].set_xdata(time_stamps)
            plots[i].set_ydata(drink.historic_prices)
            plots[i].set_label(label)
        ax.set_xlim(time_stamps[0], time_stamps[-1])
        ax.get_xaxis().set_ticks([])
        plt.legend(
            bbox_to_anchor=(0, 1.02, 1, 0.2),
            loc="lower left",
            mode="expand",
            borderaxespad=0,
            ncol=4,
            fontsize=18,
            prop=dict(weight="bold"),
        )

        # add groups
        textstr = """
        Blond
            Cornet
            Cornet Smoked
        Donker
            Grand Prestige
            La Trappe Isid'or
            La Trappe Nillis
            La Trappe Quadrupel
            Zundert 10
        Duits
            Krombacher 0.0
            Paulaner
        Duvel
            Duvel
            Duvel 666
            Duvel Tripel
        Kabouter
            Kasteel Rouge
            La Chouffe 0.4%
            La Chouffe Cherry
        Rest
            Brewdog Punk IPA
            Korenwolf
            St. Pierre Tripel
            Straffe Hendrik Tripel
            Leffe Tripel 0.0%
        Twents
            Grolsch Beugel
            Grolsch Kanon
        Zoet
            Amstel Rose
            Apple Bandit
            Budels Honing
            Leffe Ruby
            Liefmans Fruitesse
            Liefmans Peach
        Zomers
            Desperados
            Mannenliefde
            Skuumkoppe
            t IJ wit
        """
        plt.text(0.03, 0.03, textstr, fontsize=12, transform=plt.gcf().transFigure)
        plt.grid(True)

        fig.canvas.draw()
        fig.canvas.flush_events()
        print("\n")
except Exception as e:
    print(traceback.format_exc())
    quit()
