import views
import excel
import configuration
import os.path
import logging
import queue
import geoservices
import datahelpers
from solver import Solver
from datetime import datetime

TIME_LIMIT_SOLUTION_MS = 300000 # 5 minutes
MAX_VEHICLES = 100

class NotifyQueueLogHandler(logging.Handler):
    def __init__(self, queue):
        logging.Handler.__init__(self)
        self.queue = queue

    def emit(self, record):
        self.queue.put(views.emit_log(record.levelname, self.format(record)))

def handle_calculate(queue, model):
    try:
        ensure_source_file_exist(model)

        # Load the data from the input file
        entries = excel.read_locations(model.source_file)
        
        # Resolve coordinates and get time windows
        geo_helper = geoservices.GeoHelper(model.configuration["google_api_key"], model.configuration["bing_api_key"])
        addresses = []
        locations = []
        time_windows = []

        start_address = model.configuration["start_address"]
        start_coord = geo_helper.geocode(start_address)
        locations.append(start_coord)
        addresses.append(start_address)

        for entry in entries:
            address = datahelpers.get_address_from_entry(entry, model.configuration["default_country"])
            coords = geo_helper.geocode(address)
            addresses.append(address)
            locations.append(coords)
            time_windows.append(datahelpers.get_time_window_from_entry(entry))

        # Calculate distances
        matrix = geo_helper.calculate_distance_time_matrix(locations)

        # Solve
        locations_without_start = locations[1:]

        solver = Solver(start_coord, locations_without_start, time_windows, model.configuration["service_time"], MAX_VEHICLES, TIME_LIMIT_SOLUTION_MS)
        solver.travel_time_callback = travel_time_callback(locations, matrix)
        solution = solver.solve()

        if not solution:
            queue.put(views.show_message("No solution", "No solution could be found. Please adjust time windows.", views.MessageLevel.ERROR))
        else:
            excel.write_solution(solution, locations, addresses, matrix, model.destination_file)
            queue.put(views.show_message("Done", "Calculation finished! The solution has been written to the destination file.", views.MessageLevel.INFO))

    except Exception as e:
        queue.put(views.show_message("An error occurred", str(e), views.MessageLevel.ERROR))
        raise e

def travel_time_callback(locations, matrix):
    def callback(from_loc, to_loc):
        # Get time from the matrix
        entry = matrix.get_entry(from_loc, to_loc)
        if entry is None: raise ValueError("Unable to find distance/time between addresses.")
        return entry.time
    return callback

def handle_save_options(queue, config):
    configuration.save_config(config)
    queue.put(views.show_message("Saved", "The configuration has been saved.", views.MessageLevel.INFO))

def ensure_source_file_exist(model):
    # Make sure the source file exists
    if not os.path.isfile(model.source_file):
        raise ValueError("Unable to find the specified source file. Make sure the file exists.")

def configure_logger(queue):
    formatter = logging.Formatter("%(levelname)-8s %(message)s")

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    ui_handler = NotifyQueueLogHandler(queue)
    ui_handler.setLevel(logging.INFO)
    ui_handler.setFormatter(formatter)
    logger.addHandler(ui_handler)

def main():
    notify_queue = queue.Queue()

    configure_logger(notify_queue)
    config = configuration.load_config()

    main_window = views.MainWindow(notify_queue, config)
    main_window.calculate_callback = handle_calculate
    main_window.save_options_callback = handle_save_options
    main_window.mainloop()

if __name__ == '__main__':
    main()