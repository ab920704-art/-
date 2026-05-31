"""
Plague Simulator (School Project)
---------------------------------
A complete Python project inspired by Plague Inc.
Features:
- Country-based infection simulation
- Multiple disease attributes (infectivity, severity, lethality)
- Recovery system (people can recover from infection)
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
        self.recovered = 0          # 新增：康復人數
        self.lockdown = False

    @property
    def healthy(self):
        return self.population - self.infected - self.dead - self.recovered


class Disease:
    def __init__(self):
        self.infectivity = 0.15
        self.severity = 0.05
        self.lethality = 0.01
        self.recovery_rate = 0.02   # 新增：康復率，每天 2% 的感染者會康復
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

    def upgrade_recovery_resistance(self):
        # 新增：降低康復率的升級
        if self.points >= 6:
            self.points -= 6
            self.recovery_rate = max(0, self.recovery_rate - 0.01)  # 最低降到 0%
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
        total_recovered = 0

        for c in self.countries:
            if c.infected > 0:
                # lockdown chance
                if c.infected > c.population * 0.2 and not c.lockdown:
                    if random.random() < 0.1:
                        c.lockdown = True

                multiplier = 0.5 if c.lockdown else 1.0

                # 新增感染計算
                new_infections = int(c.infected * self.disease.infectivity * multiplier)
                new_infections = min(new_infections, c.healthy)

                # 新增死亡計算
                new_deaths = int(c.infected * self.disease.lethality)
                new_deaths = min(new_deaths, c.infected)

                # 新增：康復計算
                # 康復率受到嚴重程度的影響：越嚴重的病，康復越慢
                recovery_factor = max(0.1, 1.0 - self.disease.severity * 5)
                new_recoveries = int(c.infected * self.disease.recovery_rate * recovery_factor)
                new_recoveries = min(new_recoveries, c.infected - new_deaths)

                # 更新感染人數：原有感染 + 新增感染 - 新增死亡 - 新增康復
                c.infected = max(0, c.infected + new_infections - new_deaths - new_recoveries)
                c.dead += new_deaths
                c.recovered += new_recoveries

                # DNA 點數計算 - 方案一：平衡的點數系統
                # 每 50 萬人感染 = 1 點
                # 每 10 萬人死亡 = 1 點
                self.disease.points += new_infections // 500000
                self.disease.points += new_deaths // 100000

            total_infected += c.infected
            total_dead += c.dead
            total_recovered += c.recovered

        # mutation event
        if random.random() < 0.08:
            mutation_type = random.choice([
                "infectivity",
                "severity",
                "lethality",
                "recovery_resistance",  # 新增變異類型
                "incubation"
            ])

            if mutation_type == "infectivity":
                self.disease.infectivity += 0.01

            elif mutation_type == "severity":
                self.disease.severity += 0.005

            elif mutation_type == "lethality":
                self.disease.lethality += 0.003

            elif mutation_type == "recovery_resistance":
                # 新增：變異降低康復率
                self.disease.recovery_rate = max(0, self.disease.recovery_rate - 0.005)

            elif mutation_type == "incubation":
                # Longer incubation helps spreading silently
                self.disease.infectivity += 0.005
                self.cure -= 0.3

        # cure progress rises with severity
        self.cure += 0.4 + self.disease.severity * 3
        # Fix: Ensure cure stays within 0-100 range
        self.cure = max(0, min(100, self.cure))

        return total_infected, total_dead, total_recovered

    def is_win(self):
        return all(c.healthy == 0 and c.infected == 0 for c in self.countries)

    def is_lose(self):
        return self.cure >= 100


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Plague Simulator")
        self.root.geometry("900x600")

        self.game = Game()

        self.info = tk.Label(root, font=("Arial", 12), justify="left")
        self.info.pack(pady=10)

        self.country_box = tk.Text(root, height=15, width=100)
        self.country_box.pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Next Day", command=self.next_day).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Upgrade Infectivity (5)", command=self.up_inf).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Upgrade Severity (5)", command=self.up_sev).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Upgrade Lethality (8)", command=self.up_leth).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="Reduce Recovery Rate (6)", command=self.up_res).grid(row=0, column=4, padx=5)

        self.refresh()

    def refresh(self):
        g = self.game
        self.info.config(text=(
            f"Day: {g.day}    Cure: {g.cure:.1f}%    DNA Points: {g.disease.points}\n"
            f"Infectivity: {g.disease.infectivity:.2f}   "
            f"Severity: {g.disease.severity:.2f}   "
            f"Lethality: {g.disease.lethality:.2f}   "
            f"Recovery Rate: {g.disease.recovery_rate:.2f}"
        ))

        self.country_box.delete("1.0", tk.END)
        self.country_box.insert(tk.END, "Country     | Healthy        | Infected       | Recovered      | Dead           | Lockdown\n")
        self.country_box.insert(tk.END, "-" * 100 + "\n")
        for c in g.countries:
            self.country_box.insert(
                tk.END,
                f"{c.name:<11} | {c.healthy:>14,} | {c.infected:>14,} | {c.recovered:>14,} | {c.dead:>14,} | {str(c.lockdown):<8}\n"
            )

    def next_day(self):
        self.game.tick()
        self.refresh()

        if self.game.is_win():
            messagebox.showinfo("Victory", "All humans have been eliminated or recovered. You win!")
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

    def up_res(self):
        if not self.game.disease.upgrade_recovery_resistance():
            messagebox.showwarning("Not enough points", "Need 6 DNA points")
        self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
