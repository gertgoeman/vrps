from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import queue
import threading
from datetime import datetime
import dateutil.parser

class NotificationType(enum.Enum):
    SHOW_MESSAGE = 1
    EMIT_LOG = 2

class ViewModel(object):
    def __init__(self):
        self.source_file = None
        self.destination_file = None
        self.configuration = None

class MessageLevel(enum.Enum):
    INFO = 1
    ERROR = 2

def show_message(title, body, level):
    return {
        "type": NotificationType.SHOW_MESSAGE,
        "level": level,
        "title": title,
        "body": body
    }

def emit_log(level, message):
    return {
        "type": NotificationType.EMIT_LOG,
        "message": message,
        "level": level
    }

class MainWindow(Tk):
    def __init__(self, notify_queue, configuration):
        super().__init__()

        self.configuration = configuration

        self.title("Vehicle Router")
        self.geometry("400x490")

        # Add tabs
        notebook = Notebook(self)
        optimize_tab = Frame(notebook)
        options_tab = Frame(notebook)
        notebook.add(optimize_tab, text = "Optimize")
        notebook.add(options_tab, text = "Options")
        notebook.pack(fill = BOTH, expand = 1)

        # Configure tabs
        self.__create_optimize_tab(optimize_tab)
        self.__create_options_tab(options_tab)

        # Start listening for notifications
        self.notify_queue = notify_queue
        self.after(100, self.__handle_notifications)

    def __create_optimize_tab(self, optimize_tab):
        optimize_pane = PanedWindow(optimize_tab)
        optimize_pane.columnconfigure(0, weight = 1)
        optimize_pane.columnconfigure(1, weight = 0)
        optimize_pane.rowconfigure(7, weight = 1)
        optimize_pane.pack(fill = BOTH, expand = 1, padx = 10, pady = 10)

        self.__current_source = StringVar()

        lbl_source = Label(optimize_pane, text = "Select source file")
        lbl_source.grid(row = 0, column = 0, sticky = W)
        txt_source = Entry(optimize_pane, textvariable = self.__current_source)
        txt_source.grid(row = 1, column = 0, sticky = W+E)
        btn_source = Button(optimize_pane, text = "Browse", command = self.__select_source)
        btn_source.grid(row = 1, column = 1, sticky = E)

        self.__current_destination = StringVar()

        lbl_destination = Label(optimize_pane, text = "Select destination")
        lbl_destination.grid(row = 2, column = 0, sticky = W)
        txt_destination = Entry(optimize_pane, textvariable = self.__current_destination)
        txt_destination.grid(row = 3, column = 0, sticky = W+E)
        btn_destination = Button(optimize_pane, text = "Browse", command = self.__select_destination)
        btn_destination.grid(row = 3, column = 1, sticky = E)

        btn_calculate = Button(optimize_pane, text = "Calculate", command = self.__handle_calculate)
        btn_calculate.grid(row = 4, column = 0, columnspan = 2, pady = 10)

        lbl_output = Label(optimize_pane, text = "Output:")
        lbl_output.grid(row = 5, column = 0, sticky = W, pady = 5)

        frame2 = Frame(optimize_pane)
        scrollbar = Scrollbar(frame2) 
        self.__logArea = Text(frame2, state = DISABLED, yscrollcommand = scrollbar.set, borderwidth = 0, highlightthickness = 0)
        
        self.__logArea.tag_config("WARNING", foreground="orange")
        self.__logArea.tag_config("ERROR", foreground="red")
        self.__logArea.tag_config("CRITICAL", foreground="red")

        scrollbar.config(command = self.__logArea.yview)

        scrollbar.pack(side = "right", fill = Y)
        self.__logArea.pack(side = "left", fill = BOTH, expand = 1)

        frame2.grid(row = 7, column = 0, columnspan = 2, sticky = N+E+S+W)

    def __create_options_tab(self, options_tab):
        options_pane = PanedWindow(options_tab)
        options_pane.columnconfigure(0, weight = 0)
        options_pane.columnconfigure(1, weight = 1)
        options_pane.pack(fill = BOTH, expand = 1, padx = 10, pady = 10)

        self.__default_country = StringVar()
        self.__default_country.set(
            self.configuration["default_country"] if "default_country" in self.configuration else ""
        )

        lbl_country = Label(options_pane, text = "Default country:")
        lbl_country.grid(row = 0, column = 0, sticky = W)
        txt_country = Entry(options_pane, textvariable = self.__default_country)
        txt_country.grid(row = 0, column = 1, sticky = W+E)

        self.__google_api_key = StringVar()
        self.__google_api_key.set(
            self.configuration["google_api_key"] if "google_api_key" in self.configuration else ""
        )

        lbl_google_key = Label(options_pane, text = "Google API key:")
        lbl_google_key.grid(row = 1, column = 0, sticky = W)
        txt_google_key = Entry(options_pane, textvariable = self.__google_api_key)
        txt_google_key.grid(row = 1, column = 1, sticky = W+E)

        self.__bing_api_key = StringVar()
        self.__bing_api_key.set(
            self.configuration["bing_api_key"] if "bing_api_key" in self.configuration else ""
        )

        lbl_bing_key = Label(options_pane, text = "Bing API key:")
        lbl_bing_key.grid(row = 2, column = 0, sticky = W)
        txt_bing_key = Entry(options_pane, textvariable = self.__bing_api_key)
        txt_bing_key.grid(row = 2, column = 1, sticky = W+E)

        self.__service_time = StringVar()
        self.__service_time.set(
            self.configuration["service_time"] if "service_time" in self.configuration else 0
        )

        lbl_svc_time = Label(options_pane, text = "Service time (minutes):")
        lbl_svc_time.grid(row = 3, column = 0, sticky = W)
        txt_svc_time = Entry(options_pane, textvariable = self.__service_time)
        txt_svc_time.grid(row = 3, column = 1, sticky = W+E)

        self.__start_address = StringVar()
        self.__start_address.set(
            self.configuration["start_address"] if "start_address" in self.configuration else ""
        )

        lbl_start_addr = Label(options_pane, text = "Start address:")
        lbl_start_addr.grid(row = 4, column = 0, sticky = W)
        txt_start_addr = Entry(options_pane, textvariable = self.__start_address)
        txt_start_addr.grid(row = 4, column = 1, sticky = W+E)

        btn_save = Button(options_pane, text = "Save", command = self.__handle_save_options)
        btn_save.grid(row = 5, column = 0, columnspan = 2, pady = 10)

    def __select_source(self):
        source_file = filedialog.askopenfilename(initialdir = "/", title = "Select file", filetypes = [("Microsoft Office Excel Worksheet", "*.xlsx")])
        self.__current_source.set(source_file)

    def __select_destination(self):
        dest_file = filedialog.asksaveasfilename(initialdir = "/", title = "Select file", defaultextension = ".xlsx", filetypes = [("Microsoft Office Excel Worksheet", "*.xlsx")])
        self.__current_destination.set(dest_file)

    def __handle_calculate(self):
        if self.calculate_callback:
            error = self.__validate_calculate()
            if error:
                messagebox.showerror("Validation error", error)
            else:
                viewmodel = self.__create_viewmodel()
                thread = threading.Thread(target = self.calculate_callback, args=[self.notify_queue, viewmodel])
                thread.start()

    def __handle_save_options(self):
        if self.save_options_callback:
            error = self.__validate_options()
            if error:
                messagebox.showerror("Validation error", error)
            else:
                config = self.get_configuration()
                thread = threading.Thread(target = self.save_options_callback, args=[self.notify_queue, config])
                thread.start()

    def get_configuration(self):
        return {
            "default_country": self.__default_country.get(),
            "google_api_key": self.__google_api_key.get(),
            "bing_api_key": self.__bing_api_key.get(),
            "service_time": int(self.__service_time.get()),
            "start_address": self.__start_address.get()
        }

    def __validate_options(self):
        if not self.__default_country.get().strip(): return "Please enter a default country."
        if not self.__google_api_key.get().strip(): return "Please enter a google API key."
        if not self.__bing_api_key.get().strip(): return "Please enter a bing API key."
        if not self.__service_time.get().strip(): return "Please enter a service time."
        if not self.__start_address.get().strip(): return "Please enter a start address."
        
        try:
            if int(self.__service_time.get()) <= 0: return "'Service time' must be a positive number."
        except ValueError:
            return "'Service time' must be a whole number."

        return None

    def __validate_calculate(self):
        err = self.__validate_options()
        if err: return err

        if not self.__current_source.get().strip(): return "Please select a source file."
        if not self.__current_destination.get().strip(): return "Please select a destination file."

        return None

    def __create_viewmodel(self):
        result = ViewModel()
        result.source_file = self.__current_source.get()
        result.destination_file = self.__current_destination.get()
        result.configuration = self.get_configuration()
        return result

    def __handle_notifications(self):
        try:
            result = self.notify_queue.get(0)
            notification_type = result["type"]

            if notification_type == NotificationType.SHOW_MESSAGE:
                self.__show_message(result)
            elif notification_type == NotificationType.EMIT_LOG:
                self.__emit_log(result)

        except queue.Empty:
            pass
                
        self.after(100, self.__handle_notifications)

    def __show_message(self, data):
        level = data["level"]
        title = data["title"]
        body = data["body"]
        
        if level == MessageLevel.INFO:
            messagebox.showinfo(title, body)
        elif level == MessageLevel.ERROR:
            messagebox.showerror(title, body)

    def __emit_log(self, data):
        self.__logArea.configure(state = NORMAL)
        self.__logArea.insert(END, data["message"] + "\n", data["level"])
        self.__logArea.see(END)
        self.__logArea.configure(state = DISABLED)
