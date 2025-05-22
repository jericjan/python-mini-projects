
import json
from typing import Any, Callable, Literal, TypedDict, overload
import re


class Expense(TypedDict):
    description: str
    amount: float


def strip_ansi(txt: str):
    return re.sub(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]', '', txt)


class TextBoxer:
    def __init__(self, lines: list[str] = []):
        self.lines: list[str] = lines

    def __add__(self, other: str):
        return TextBoxer(self.lines + [other])

    def print(self):
        get_len: Callable[[str], int] = lambda x: len(strip_ansi(x))
        max_width = max(map(get_len, self.lines))
        print("█" * (max_width + 4))
        print("█ " + " " * max_width + " █")
        for line in self.lines:
            stripped_len = len(strip_ansi(line))
            print("█ " + line + " " * (max_width - stripped_len) + " █")
        print("█ " + " " * max_width + " █")
        print("█" * (max_width + 4))


def add_expense(budget: float, expenses: list[Expense]):
    if get_balance(budget, expenses) < 0:
        if yes_or_no("You are already over the budget. Continue?") is False:
            return

    description = input("Enter expense description: ")
    amount = ask_for_number(f"Enter expense amount (You have {get_balance(budget, expenses)} balance left): ")

    if (get_balance(budget, expenses) - amount) < 0:
        if yes_or_no("Adding this will put you over the budget. Continue?") is False:
            return
    expenses.append({"description": description, "amount": amount})
    print(f"Added expense: {description}, Amount: {amount}")


def get_total_expenses(expenses: list[Expense]):
    return sum(expense['amount'] for expense in expenses)


def get_balance(budget: float, expenses: list[Expense]):
    return budget - get_total_expenses(expenses)


def show_budget_details(budget: float, expenses: list[Expense]):
    boxer = TextBoxer()
    boxer += f"\x1b[33mTotal Budget: {budget}\x1b[0m"
    boxer += "Expenses:"
    for expense in expenses:
        boxer += f"- {expense['description']}: {expense['amount']}"
    boxer += f"Total Spent: {get_total_expenses(expenses)}"
    balance = get_balance(budget, expenses)
    boxer += f"Remaining Budget: \x1b[3{1 if balance < 0 else 2}m{balance}\x1b[0m"
    boxer.print()


def load_budget_data(filepath: str) -> tuple[float, list[Expense]]:
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            return data['initial_budget'], data['expenses']
    except (FileNotFoundError, json.JSONDecodeError):
        return 0, []  # Return default values if the file doesn't exist or is empty/corrupted


def select_expense(expenses: list[Expense], msg: str):
    """Returns an index of the expense you want to delete"""
    for idx, expense in enumerate(expenses):
        print(f"{idx} - {expense['description']}: {expense['amount']}")
    while True:
        choice = ask_for_number(msg, "int")
        if choice not in range(len(expenses)):
            print("That's not one of the items!", end="")
            move_up(1)
            clear_line()
        else:
            clear_line()
            break
    return choice


def delete_budget_details(expenses: list[Expense]):
    if len(expenses) == 0:
        print("You have no expenses. Add one first.")
        return
    choice = select_expense(expenses, "Enter the # of the item you want to delete: ")
    deleted = expenses.pop(choice)
    print(f"\"{deleted['description']} - {deleted['amount']}\" has been deleted.")


def edit_budget_details(expenses: list[Expense]):
    if len(expenses) == 0:
        print("You have no expenses. Add one first.")
        return
    choice = select_expense(expenses, "Enter the # of the item you want to edit: ")
    print("1. Edit description")
    print("2. Edit amount")
    while True:
        mode = input("What do you want to edit? ")
        if mode == "1":
            clear_line()
            expenses[choice]['description'] = input(f"{expenses[choice]['description']} -> ")            
            break
        elif mode == "2":
            clear_line()
            expenses[choice]['amount'] = ask_for_number(f"{expenses[choice]['amount']} -> ")            
            break
        else:
            print("That's not one of the options!", end="")
            move_up(1)
            clear_line()


def save_budget_data(filepath: str, initial_budget: float, expenses: list[Expense]):
    data: dict[str, Any] = {
        'initial_budget': initial_budget,
        'expenses': expenses
    }
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)


@overload
def ask_for_number(msg: str, type: Literal['float']) -> float:
    ...


@overload
def ask_for_number(msg: str, type: Literal['int']) -> int:
    ...


@overload
def ask_for_number(msg: str) -> float:
    ...


def ask_for_number(msg: str, type: str = 'float'):
    while True:
        try:
            if type == "float":
                out = float(input(msg))
            elif type == "int":
                out = int(input(msg))
            else:
                raise ValueError("Invalid `type` value")
            clear_line()
            return out
        except ValueError:
            clear_line()
            print("That's not a number!", end="")
            move_up(1)
            clear_line()


def yes_or_no(msg: str):
    while True:
        choice = input(msg + " (y/n) ")
        if choice == "y":
            clear_line()
            return True
        elif choice == "n":
            clear_line()
            return False
        else:
            print("That's not one of the options!", end="")
            move_up(1)
            clear_line()


def clear_screen():
    """Clears screen and moves cursor back to top"""
    print("\x1b[2J\x1b[H", end="")


def clear_line():
    print("\x1b[2K\r", end="")


def move_up(times: int):
    print(f"\x1b[{times}A", end="")  # Moves up


def main():
    clear_screen()
    print("Welcome to the Budget App")
    filepath = 'budget_data.json'  # Define the path to your JSON file
    initial_budget, expenses = load_budget_data(filepath)
    if initial_budget == 0:
        initial_budget = ask_for_number("Please enter your initial budget: ")

    while True:
        menu_items = [
            "\n",
            "1. Add an expense",
            "2. Show budget details",
            "3. Delete an expense",
            "4. Edit an expense",
            "5. Edit budget",
            "6. Exit and Save"
        ]
        for x in menu_items:
            print(x)

        move_up(len(menu_items))
        choice = input("Enter the # your choice: ")
        clear_screen()
        if choice == "1":
            add_expense(initial_budget, expenses)
        elif choice == "2":
            show_budget_details(initial_budget, expenses)
        elif choice == "3":
            delete_budget_details(expenses)
        elif choice == "4":
            edit_budget_details(expenses)
        elif choice == "5":
            print(f"Your current budget is: {initial_budget}")
            initial_budget = ask_for_number("Enter your new budget: ")
        elif choice == "6":
            save_budget_data(filepath, initial_budget, expenses)
            print("Saving changes and exiting Budget App. Goodbye!")
            break
        else:
            print("Invalid choice, please choose again.")


if __name__ == "__main__":
    main()
