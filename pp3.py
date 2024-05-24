import tkinter as tk
from tkinter import simpledialog
from datetime import timedelta, datetime
import pickle
import os

LOG_FILE = "timer_log.pkl"

class Timer:
    def __init__(self, app, master, timer_number, duration=5405, remaining=None, running=False, start_time=None):
        self.app = app
        self.master = master
        self.timer_number = timer_number
        self.original_duration = duration  # 초기 duration 저장
        self.duration = duration
        self.remaining = remaining if remaining is not None else duration
        self.running = running
        self.start_time = start_time

        self.number_label = tk.Label(master, text=f"{timer_number}", font=('Helvetica', 20), fg="green")
        self.number_label.grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.display = tk.Label(master, text=self.format_time(self.remaining), font=('Helvetica', 20))
        self.display.grid(row=1, column=0, columnspan=2, sticky="nsew")

        self.check_button = tk.Button(master, text="✔", fg="orange", command=self.change_button_color, font=('Helvetica', 14))
        self.check_button.grid(row=2, column=0, columnspan=2, sticky="nsew")
        self.check_button.grid_remove()  # Initially hide this button
        
        self.start_stop_button = tk.Button(master, text="Start", command=self.start_stop, font=('Helvetica', 11))
        self.start_stop_button.grid(row=3, column=0, sticky="nsew")
        
        self.reset_button = tk.Button(master, text="Reset", command=self.reset, font=('Helvetica', 11))
        self.reset_button.grid(row=3, column=1, sticky="nsew")

        self.set_duration_button = tk.Button(master, text="Set Duration", command=self.set_duration, font=('Helvetica', 11))
        self.set_duration_button.grid(row=4, column=0, columnspan=2, sticky="nsew")

        self.start_time_label = tk.Label(master, text="", font=('Helvetica', 10))
        self.start_time_label.grid(row=5, column=0, columnspan=2, sticky="nsew")

        if self.start_time:
            self.start_time_label.config(text=f"Started at: {self.start_time.strftime('%H:%M:%S')}")
        if self.running:
            self.start_stop_button.config(text="Pause")
            self.tick()
        else:
            self.app.update_status()  # Ensure status is updated if timer is not running

    def tick(self):
        if self.running and self.remaining > 0:
            self.remaining -= 1
            self.display.config(text=self.format_time(self.remaining))
            if self.remaining <= 1200:  # Less than 10 minutes
                self.number_label.config(fg="orange")
                if not self.check_button.winfo_viewable():  # Check if the button is hidden
                    self.check_button.grid()  # Show the button
            if self.remaining == 0:  # Time is up
                self.number_label.config(fg="red")
                self.check_button.grid_remove()  # Ensure the button is hidden
            self.master.after(1000, self.tick)
            self.app.update_status()
        elif self.remaining == 0:
            self.running = False
            self.start_stop_button.config(text="Start")
            self.number_label.config(fg="red")
            self.check_button.grid_remove()
            self.app.update_status()

    def start_stop(self):
        if not self.running:
            if self.start_time is None:  # Only update the start time if it is None
                self.start_time = datetime.now()  # 현재 시각 저장
                start_time_str = self.start_time.strftime('%H:%M:%S')
                self.start_time_label.config(text=f"Started at: {start_time_str}")
                print(f"Timer {self.timer_number} Started at: {start_time_str}")  # 콘솔에 출력
        self.running = not self.running
        self.start_stop_button.config(text="Pause" if self.running else "Start")
        if self.running:
            self.number_label.config(fg="black")  # Change color when timer starts
            self.tick()
        self.app.update_status()

    def change_button_color(self):
        self.check_button.config(fg="green")  # Change the button color to green

    def reset(self):
        self.running = False
        self.original_duration = 5400  # Reset duration to 5400 seconds
        self.duration = 5400  # Reset duration to 5400 seconds
        self.remaining = self.duration
        self.display.config(text=self.format_time(self.remaining))
        self.number_label.config(fg="green")  # Reset color to green
        self.check_button.grid_remove()  # Ensure the button is hidden
        self.check_button.config(fg="orange")  # Reset button color to orange
        self.start_time = None  # Reset the start time
        self.start_time_label.config(text="")  # Clear the start time label
        self.app.update_status()

    def set_duration(self):
        new_duration = simpledialog.askinteger("Set Duration", "Enter new duration in seconds:", parent=self.master)
        if new_duration is not None and new_duration > 0:
            self.original_duration = new_duration
            self.duration = new_duration
            self.remaining = new_duration
            self.display.config(text=self.format_time(self.remaining))  # Update display immediately

    def format_time(self, seconds):
        return str(timedelta(seconds=seconds))

    def get_state(self):
        return {
            'timer_number': self.timer_number,
            'duration': self.duration,
            'remaining': self.remaining,
            'running': self.running,
            'start_time': self.start_time,
        }

class MultiTimerApp:
    def __init__(self, master):
        self.master = master
        self.timers = []
        self.load_state()
        
        self.status_label = tk.Label(master, text="", font=('Helvetica', 24))
        self.status_label.grid(row=5, column=0, columnspan=10, sticky="nsew")

        timer_number = 1
        for i in range(5):
            for j in range(10):
                frame = tk.Frame(master, padx=5, pady=5)
                frame.grid(row=i, column=j, sticky="nsew")
                state = self.saved_state.get(timer_number, {})
                timer = Timer(
                    self, frame, timer_number,
                    duration=state.get('duration', 5405),
                    remaining=state.get('remaining'),
                    running=state.get('running', False),
                    start_time=state.get('start_time')
                )
                self.timers.append(timer)
                timer_number += 1

        for i in range(5):
            master.grid_rowconfigure(i, weight=1, minsize=50)

        for j in range(10):
            master.grid_columnconfigure(j, weight=1, minsize=100)
        
        self.update_status()
        self.save_state_periodically()

    def update_status(self):
        non_initial_timers = sum(1 for timer in self.timers if timer.remaining != timer.duration)
        timers_below_10_minutes = sum(1 for timer in self.timers if timer.remaining <= 600)
        inactive_timers = sum(1 for timer in self.timers if not timer.running)
        self.status_label.config(text=f"입장가능: {inactive_timers}, 작동 중: {non_initial_timers}, 10분 이하: {timers_below_10_minutes}")
        self.master.after(1000, self.update_status)

    def save_state_periodically(self):
        self.save_state()
        self.master.after(300000, self.save_state_periodically)  # 5 minutes in milliseconds

    def save_state(self):
        state = {timer.timer_number: timer.get_state() for timer in self.timers}
        with open(LOG_FILE, 'wb') as f:
            pickle.dump(state, f)

    def load_state(self):
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'rb') as f:
                self.saved_state = pickle.load(f)
        else:
            self.saved_state = {}

root = tk.Tk()
root.title("멀티 타이머 앱")
app = MultiTimerApp(root)
root.attributes('-fullscreen', True)
root.mainloop()
