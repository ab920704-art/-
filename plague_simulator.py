"""
瘟疫模擬器 (學校專案)
---------------------------------
完整的 Python 專案，靈感來自 Plague Inc.
功能：
- 以國家為基礎的感染模擬
- 多種疾病屬性（傳染性、嚴重程度、致命性）
- 康復系統（感染者可以康復，具有隨機變化）
- 國家間傳播（病毒在國家之間傳播）
- 強化的封城系統（明確顯示和更高的影響力）
- 變異事件
- 治療進度系統
- 勝負條件
- Tkinter GUI（僅使用標準庫）

運行：python plague_simulator.py
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
        self.recovered = 0          # 康復人數
        self.lockdown = False
        self.lockdown_notified = False  # 記錄是否已通知玩家封城

    @property
    def healthy(self):
        return self.population - self.infected - self.dead - self.recovered


class Disease:
    def __init__(self):
        self.infectivity = 0.15
        self.severity = 0.05
        self.lethality = 0.01
        self.recovery_rate = 0.02   # 康復率：每天 2% 的感染者會康復
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
        # 降低康復率的升級
        if self.points >= 6:
            self.points -= 6
            self.recovery_rate = max(0, self.recovery_rate - 0.01)  # 最低降到 0%
            return True
        return False


class Game:
    def __init__(self, lockdown_callback=None):
        self.day = 0
        self.cure = 0
        self.disease = Disease()
        self.countries = [
            Country("美國", 330_000_000),
            Country("台灣", 23_000_000),
            Country("日本", 125_000_000),
            Country("印度", 1_400_000_000),
            Country("巴西", 214_000_000),
        ]
        self.lockdown_callback = lockdown_callback  # 用於通知 UI 有新的封城

        # 在一個隨機國家開始感染
        start = random.choice(self.countries)
        start.infected = 100

    def tick(self):
        self.day += 1

        total_infected = 0
        total_dead = 0
        total_recovered = 0

        for c in self.countries:
            if c.infected > 0:
                # 封鎖概率 - 改進：觸發條件更容易
                if c.infected > c.population * 0.2 and not c.lockdown:
                    if random.random() < 0.1:
                        c.lockdown = True
                        # 觸發通知回調
                        if self.lockdown_callback:
                            self.lockdown_callback(c)

                # 改進：封城時傳染性更低（0.3 instead of 0.5）
                multiplier = 0.3 if c.lockdown else 1.0

                # 新增感染計算
                new_infections = int(c.infected * self.disease.infectivity * multiplier)
                new_infections = min(new_infections, c.healthy)

                # 新增死亡計算
                new_deaths = int(c.infected * self.disease.lethality)
                new_deaths = min(new_deaths, c.infected)

                # 康復計算（隨機因子）
                # 康復率受到嚴重程度的影響：越嚴重的病，康復越慢
                recovery_factor = max(0.1, 1.0 - self.disease.severity * 5)
                
                # 改進：封城時康復率提升（× 1.5）
                if c.lockdown:
                    recovery_factor *= 1.5
                
                # 隨機性：0.5 到 1.0 之間的隨機倍數
                random_recovery_multiplier = random.uniform(0.5, 1.0)
                new_recoveries = int(c.infected * self.disease.recovery_rate * recovery_factor * random_recovery_multiplier)
                new_recoveries = min(new_recoveries, c.infected - new_deaths)

                # 更新感染人數：原有感染 + 新增感染 - 新增死亡 - 新增康復
                c.infected = max(0, c.infected + new_infections - new_deaths - new_recoveries)
                c.dead += new_deaths
                c.recovered += new_recoveries

                # DNA 點數計算 - 平衡的點數系統
                # 每 50 萬人感染 = 1 點
                # 每 10 萬人死亡 = 1 點
                self.disease.points += new_infections // 500000
                self.disease.points += new_deaths // 100000

            total_infected += c.infected
            total_dead += c.dead
            total_recovered += c.recovered

        # 方案 B - 基於感染程度的國家間傳播
        self.spread_to_other_countries()

        # 變異事件
        if random.random() < 0.08:
            mutation_type = random.choice([
                "infectivity",
                "severity",
                "lethality",
                "recovery_resistance",
                "incubation"
            ])

            if mutation_type == "infectivity":
                self.disease.infectivity += 0.01

            elif mutation_type == "severity":
                self.disease.severity += 0.005

            elif mutation_type == "lethality":
                self.disease.lethality += 0.003

            elif mutation_type == "recovery_resistance":
                # 變異降低康復率
                self.disease.recovery_rate = max(0, self.disease.recovery_rate - 0.005)

            elif mutation_type == "incubation":
                # 更長的潛伏期有利於無聲傳播
                self.disease.infectivity += 0.005
                self.cure -= 0.3

        # 治療進度隨嚴重程度上升
        self.cure += 0.4 + self.disease.severity * 3
        
        # 改進：封城國家會加快治療進度
        for c in self.countries:
            if c.lockdown:
                self.cure += 1.5  # 每個封城國家加速 1.5%/天
        
        # 確保治療進度在 0-100 範圍內
        self.cure = max(0, min(100, self.cure))

        return total_infected, total_dead, total_recovered

    def spread_to_other_countries(self):
        """
        方案 B：基於感染程度的國家間傳播
        感染人數越多，傳播到其他國家的概率越高
        """
        for c in self.countries:
            if c.infected > 1000:  # 感染者 > 1000 人時才會傳播
                # 計算傳播概率：感染人數占該國人口的比例
                # 感染比例越高，傳播概率越高（最多 50%）
                infection_ratio = c.infected / c.population
                spread_chance = min(0.5, infection_ratio * 100)
                
                # 改進：封城時傳播概率降低
                if c.lockdown:
                    spread_chance *= 0.5

                # 隨機選擇其他國家
                other_countries = [other for other in self.countries if other != c]

                for other in other_countries:
                    # 如果該國還沒有感染者，才會被傳染
                    if other.infected == 0 and random.random() < spread_chance:
                        # 傳入 10-50 個感染者
                        other.infected = random.randint(10, 50)

                    # 如果該國已有感染者，概率較低地傳播更多病例
                    elif other.infected > 0 and random.random() < spread_chance * 0.3:
                        # 額外傳入 5-20 個感染者
                        other.infected += random.randint(5, 20)

    def is_win(self):
        return all(c.healthy == 0 and c.infected == 0 for c in self.countries)

    def is_lose(self):
        return self.cure >= 100


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("瘟疫模擬器")
        self.root.geometry("1000x700")

        self.game = Game(lockdown_callback=self.on_lockdown)

        # 標題信息
        self.info = tk.Label(root, font=("Arial", 12), justify="left", fg="black")
        self.info.pack(pady=10)

        # 封城信息面板
        self.lockdown_info = tk.Label(root, font=("Arial", 10), justify="left", fg="red")
        self.lockdown_info.pack(pady=5)

        # 國家數據表
        self.country_box = tk.Text(root, height=15, width=120, font=("Arial", 9))
        self.country_box.pack(padx=10)

        # 按鈕框架
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="下一天", command=self.next_day, font=("Arial", 10), width=12).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="升級傳染性 (5)", command=self.up_inf, font=("Arial", 10), width=14).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="升級嚴重程度 (5)", command=self.up_sev, font=("Arial", 10), width=14).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="升級致命性 (8)", command=self.up_leth, font=("Arial", 10), width=12).grid(row=0, column=3, padx=5)
        tk.Button(btn_frame, text="降低康復率 (6)", command=self.up_res, font=("Arial", 10), width=14).grid(row=0, column=4, padx=5)

        self.refresh()

    def on_lockdown(self, country):
        """當某個國家實施封城時的回調"""
        messagebox.showwarning(
            "⚠️ 封城警告",
            f"{country.name}已實施封城！\n\n"
            f"📉 傳染性降低至 30%（原本 100%）\n"
            f"💊 治療進度加快 +1.5%/天\n"
            f"💪 人口康復速度提升 50%\n\n"
            f"難度大幅提升！需要盡快感染其他國家。"
        )

    def refresh(self):
        g = self.game
        
        # 更新主要信息
        self.info.config(text=(
            f"天數：{g.day}    治療進度：{g.cure:.1f}%    DNA 點數：{g.disease.points}\n"
            f"傳染性：{g.disease.infectivity:.2f}   "
            f"嚴重程度：{g.disease.severity:.2f}   "
            f"致命性：{g.disease.lethality:.2f}   "
            f"康復率：{g.disease.recovery_rate:.2f}"
        ))

        # 更新封城信息
        lockdown_countries = [c.name for c in g.countries if c.lockdown]
        if lockdown_countries:
            lockdown_info_text = f"🔒 已封城國家：{', '.join(lockdown_countries)}"
            lockdown_info_text += f"  | 傳染性 -70%  | 治療進度 +{len(lockdown_countries)*1.5:.1f}%/天"
            self.lockdown_info.config(text=lockdown_info_text, fg="red")
        else:
            self.lockdown_info.config(text="✅ 暫無封城國家", fg="green")

        # 更新國家數據表
        self.country_box.delete("1.0", tk.END)
        self.country_box.insert(tk.END, "國家    | 健康人口         | 感染人數         | 康復人數         | 死亡人數         | 感染率    | 封城狀態\n")
        self.country_box.insert(tk.END, "-" * 130 + "\n")
        
        for c in g.countries:
            infection_rate = (c.infected / c.population) * 100
            lockdown_status = "🔒 已封城" if c.lockdown else "✅ 正常"
            lockdown_color_code = ""
            
            self.country_box.insert(
                tk.END,
                f"{c.name:<6} | {c.healthy:>16,} | {c.infected:>16,} | {c.recovered:>16,} | {c.dead:>16,} | {infection_rate:>7.2f}% | {lockdown_status:<10}\n"
            )

    def next_day(self):
        self.game.tick()
        self.refresh()

        if self.game.is_win():
            messagebox.showinfo(
                "🎉 勝利",
                "所有人類已被消滅或康復。\n\n"
                f"遊戲耗時：{self.game.day} 天\n"
                f"最終傳染性：{self.game.disease.infectivity:.2f}\n"
                f"最終嚴重程度：{self.game.disease.severity:.2f}\n"
                f"最終致命性：{self.game.disease.lethality:.2f}\n\n"
                "你贏了！"
            )
            self.root.quit()

        if self.game.is_lose():
            messagebox.showerror(
                "💀 失敗",
                "治療進度達到 100%。\n\n"
                f"遊戲進行了 {self.game.day} 天\n"
                f"感染人數：{sum(c.infected for c in self.game.countries):,} 人\n"
                f"死亡人數：{sum(c.dead for c in self.game.countries):,} 人\n\n"
                "科學家成功研發出治療方案。\n你輸了！"
            )
            self.root.quit()

    def up_inf(self):
        if not self.game.disease.upgrade_infectivity():
            messagebox.showwarning("點數不足", "需要 5 個 DNA 點數")
        self.refresh()

    def up_sev(self):
        if not self.game.disease.upgrade_severity():
            messagebox.showwarning("點數不足", "需要 5 個 DNA 點數")
        self.refresh()

    def up_leth(self):
        if not self.game.disease.upgrade_lethality():
            messagebox.showwarning("點數不足", "需要 8 個 DNA 點數")
        self.refresh()

    def up_res(self):
        if not self.game.disease.upgrade_recovery_resistance():
            messagebox.showwarning("點數不足", "需要 6 個 DNA 點數")
        self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
