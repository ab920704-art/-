"""
Plague Simulator (School Project)
---------------------------------
A complete Python project inspired by Plague Inc.
Features:
- Country-based infection simulation
- Multiple disease attributes (infectivity, severity, lethality)
- Mutation events
- Cure progress system
- Win/Lose conditions
- Tkinter GUI (standard library only)

Run: python plague_simulator.py
"""

import tkinter as tk
from tkinter import messagebox
import random


class Country:
    def __init__(self, name, population):
        self.name = name
        self.population = population
        self.infected = 0
        self.dead = 0
        self.lockdown = False

    @property
    def healthy(self):
        return self.population - self.infected - self.dead


class Disease:
    def __init__(self):
        self.infectivity = 0.15
        self.severity = 0.05
        self.lethality = 0.01
        self.points = 0

    def upgrade_infectivity(self):
        if self.points >= 5:
            self.points -= 5
            self.infectivity += 0.05
            return True
        return False

    def upgrade_severity(self):
        if self.points >= 5:
            self.points -= 5
            self.severity += 0.03
            return True
        return False

    def upgrade_lethality(self):
        if self.points >= 8:
            self.points -= 8
            self.lethality += 0.02
            return True
        return False


class Game:
    def __init__(self):
        self.day = 0
        self.cure = 0
        self.disease = Disease()
        self.countries = [
            Country("USA", 330_000_000),
            Country("Taiwan", 23_000_000),
            Country("Japan", 125_000_000),
            Country("India", 1_400_000_000),
            Country("Brazil", 214_000_000),
        ]

        # Start infection in one random country
        start = random.choice(self.countries)
        start.infected = 100

    def tick(self):
        self.day += 1

        total_infected = 0
        total_dead = 0

        for c in self.countries:
            if c.infected > 0:
                # lockdown chance
                if c.infected > c.population * 0.2 and not c.lockdown:
                    if random.random() < 0.1:
                        c.lockdown = True

                multiplier = 0.5 if c.lockdown else 1.0

                new_infections = int(c.infected * self.disease.infectivity * multiplier)
                new_infections = min(new_infections, c.healthy)

                new_deaths = int(c.infected * self.disease.lethality)
                new_deaths = min(new_deaths, c.infected)

                # Fix: Ensure infected count doesn't go negative
                c.infected = max(0, c.infected + new_infections - new_deaths)
                c.dead += new_deaths

                self.disease.points += max(1, new_infections // 100000)

            total_infected += c.infected
            total_dead += c.dead

        # mutation event
        if random.random() < 0.08:
            mutation_type = random.choice([
                "infectivity",
                "severity",
                "lethality",
                "incubation"
            ])

            if mutation_type == "infectivity":
                self.disease.infectivity += 0.01

            elif mutation_type == "severity":
                self.disease.severity += 0.005

            elif mutation_type == "lethality":
                self.disease.lethality += 0.003

            elif mutation_type == "incubation":
                # Longer incubation helps spreading silently
                self.disease.infectivity += 0.005
                self.cure -= 0.3

        # cure progress rises with severity
        self.cure += 0.4 + self.disease.severity * 3
        # Fix: Ensure cure stays within 0-100 range
        self.cure = max(0, min(100, self.cure))

        return total_infected, total_dead

    def is_win(self):
        return all(c.healthy == 0 and c.infected == 0 for c in self.countries)

    def is_lose(self):
        return self.cure >= 100


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Plague Simulator")
        self.root.geometry("700x500")

        self.game = Game()

        self.info = tk.Label(root, font=("Arial", 12), justify="left")
        self.info.pack(pady=10)

        self.country_box = tk.Text(root, height=15, width=80)
        self.country_box.pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Next Day", command=self.next_day).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Upgrade Infectivity (5)", command=self.up_inf).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Upgrade Severity (5)", command=self.up_sev).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Upgrade Lethality (8)", command=self.up_leth).grid(row=0, column=3, padx=5)

        self.refresh()

    def refresh(self):
        g = self.game
        self.info.config(text=(
            f"Day: {g.day}    Cure: {g.cure:.1f}%    DNA Points: {g.disease.points}\n"
            f"Infectivity: {g.disease.infectivity:.2f}   "
            f"Severity: {g.disease.severity:.2f}   "
            f"Lethality: {g.disease.lethality:.2f}"
        ))

        self.country_box.delete("1.0", tk.END)
        for c in g.countries:
            self.country_box.insert(
                tk.END,
                f"{c.name:<10} | Healthy: {c.healthy:,} | Infected: {c.infected:,} | Dead: {c.dead:,} | Lockdown: {c.lockdown}\n"
            )

    def next_day(self):
        self.game.tick()
        self.refresh()

        if self.game.is_win():
            messagebox.showinfo("Victory", "All humans have been eliminated. You win!")
            self.root.quit()

        if self.game.is_lose():
            messagebox.showerror("Defeat", "The cure reached 100%. You lose!")
            self.root.quit()

    def up_inf(self):
        if not self.game.disease.upgrade_infectivity():
            messagebox.showwarning("Not enough points", "Need 5 DNA points")
        self.refresh()

    def up_sev(self):
        if not self.game.disease.upgrade_severity():
            messagebox.showwarning("Not enough points", "Need 5 DNA points")
        self.refresh()

    def up_leth(self):
        if not self.game.disease.upgrade_lethality():
            messagebox.showwarning("Not enough points", "Need 8 DNA points")
        self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
