import openpyxl
import datetime

def read_locations(path):
    wb = openpyxl.load_workbook(filename = path)
    ws = wb.active

    colnames = ["street", "nr", "bus", "state", "postal code", "city", "country", "start time", "end time"]

    first_row = next(ws.rows)
    col_indices = { n: cell.value.lower() for n, cell in enumerate(first_row)
                    if cell.value and cell.value.lower() in colnames }

    entries = []

    for i, row in enumerate(ws.rows):
        if i == 0: continue     # the first row contains the headers
        entry = {}
        for index, cell in enumerate(row):
            if index in col_indices:
                if cell.value is None: continue

                colname = col_indices[index]
                entry[colname] = str(cell.value)

        # Validate entry
        if "start time" not in entry:
            raise ValueError("Unable to find 'Start Time' for entry in excel sheet.")
        if "end time" not in entry:
            raise ValueError("Unable to find 'End Time' for entry in excel sheet.")

        entries.append(entry)

    return entries

def write_solution(solution, locations, addresses, matrix, path):
    wb = openpyxl.Workbook()

    i = 0
    for vehicle in solution.vehicles:
        # There must be at least 3 locations for the vehicle (depot + 1 destination + depot)
        if len(vehicle.nodes) < 3: continue

        # Create a sheet for the vehicle
        if i == 0:
            ws = wb.active
            ws.title = "Vehicle " + str(i + 1)
        else:
            ws = wb.create_sheet(title = "Vehicle " + str(i + 1))

        i = i + 1

        # Insert headers
        ws.append([ "Address", "Approx time" ])

        # Append nodes to the worksheet
        for i, node in enumerate(vehicle.nodes):
            if not node.location in locations: raise ValueError("Unknown location: " + str(node.location))

            loc_idx = locations.index(node.location)
            address = addresses[loc_idx]

            # The start time in the depot = arrival(first location) - travel_time
            if i == 0:
                next_time = vehicle.nodes[1].time
                dist_time = matrix.get_entry(node.location, vehicle.nodes[1].location)
                seconds = next_time - dist_time.time
            else:
                seconds = node.time

            time = str(datetime.timedelta(seconds = seconds))

            ws.append([address, time])

    wb.save(filename = path)