from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import logging

logger = logging.getLogger()

class Node(object):
    def __init__(self, location, time):
        self.location = location
        self.time = time

class Vehicle(object):
    def __init__(self, nodes):
        self.nodes = nodes

class Solution(object):
    def __init__(self, vehicles):
        self.vehicles = vehicles

class Solver(object):
    def __init__(self, start_location, locations, time_windows, service_time, num_vehicles, time_limit_ms):
        if (len(locations) == 0): raise ValueError("Argument 'locations' cannot be empty.")
        if (len(time_windows) != len(locations)): raise ValueError("A time windows must be specified for every location except the start/end location.")
        if (num_vehicles <= 0): raise ValueError("Argument 'num_vehicles' must be greater than 0.")
        if (time_limit_ms <= 0): raise ValueError("Argument 'time_limit_ms' must be greater than 0.")

        self.locations = locations
        self.time_windows = time_windows
        self.num_vehicles = num_vehicles
        self.service_time = service_time
        self.time_limit_ms = time_limit_ms

        # Add start location with time windows of 0.
        self.locations.insert(0, start_location)
        self.time_windows.insert(0, (0, 0))

    @property 
    def travel_time_callback(self):
        return self.__travel_time_callback

    @travel_time_callback.setter
    def travel_time_callback(self, value):
        self.__travel_time_callback = value

    @property 
    def travel_distance_callback(self):
        return self.__travel_distance_callback

    @travel_distance_callback.setter
    def travel_distance_callback(self, value):
        self.__travel_distance_callback = value

    # The total time is the time calculated by the travel_time_callback + the service time
    def __total_time_callback(self, from_node, to_node):
        actual_from_node = self.locations[from_node]
        actual_to_node = self.locations[to_node]

        return self.travel_time_callback(actual_from_node, actual_to_node) + self.service_time

    def __total_distance_callback(self, from_node, to_node):
        actual_from_node = self.locations[from_node]
        actual_to_node = self.locations[to_node]

        return self.travel_distance_callback(actual_from_node, actual_to_node)

    def solve(self):
        logger.info("Calculating solution.")

        depot = 0
        num_locations = len(self.locations)

        routing = pywrapcp.RoutingModel(num_locations, self.num_vehicles, depot)
        search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()

        # Set heuristics and time limit
        search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search_parameters.time_limit_ms = self.time_limit_ms

        # Add fixed dimension to count the number of nodes per vehicle
        always_one = "Always One"

        routing.AddConstantDimension(
            1,
            1000,  # Max 1000 nodes seems more than enough
            True,
            always_one)

        for vehicle_nbr in range(self.num_vehicles):
            var = routing.CumulVar(routing.End(vehicle_nbr), always_one)
            routing.AddVariableMaximizedByFinalizer(var)

        # Add distance dimension.
        dist_horizon = 10000000 # (in meters) Used as both the upper bound for the slack variable (maximum amount of distance between 2 nodes) and the upper bound for the cummulative variable (total maximum amount of distance).
        distance = "Distance"
        dist_fix_start_cumul_to_zero_time = True

        total_distance_callback = self.__total_distance_callback

        routing.SetArcCostEvaluatorOfAllVehicles(total_distance_callback)

        # Add time dimension.
        time_horizon = 24 * 3600 # Used as both the upper bound for the slack variable (maximum amount of time between 2 nodes) and the upper bound for the cummulative variable (total maximum amount of time).
        time = "Time"
        time_fix_start_cumul_to_zero_time = True

        total_time_callback = self.__total_time_callback # I honestly have no idea why this is necessary, but if I don't do it, a segmentation fault is thrown.

        routing.AddDimension(total_time_callback,
                             time_horizon,
                             time_horizon,
                             time_fix_start_cumul_to_zero_time,
                             time)

        # Add time window constraints.
        time_dimension = routing.GetDimensionOrDie(time)

        for location in range(1, num_locations):
            start = self.time_windows[location][0]
            end = self.time_windows[location][1]
            time_dimension.CumulVar(location).SetRange(start, end)

        # Solve the problem.
        assignment = routing.SolveWithParameters(search_parameters)
        
        # No solution, nothing to return.
        if not assignment: return None

        # Create the solution
        time_dimension = routing.GetDimensionOrDie(time);

        vehicles = []

        for vehicle_nbr in range(self.num_vehicles):
            index = routing.Start(vehicle_nbr)

            nodes = []

            while not routing.IsEnd(index):
                node_index = routing.IndexToNode(index)
                time_var = time_dimension.CumulVar(index)
                nodes.append(Node(self.locations[node_index], assignment.Value(time_var)))
                index = assignment.Value(routing.NextVar(index))

            node_index = routing.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            nodes.append(Node(self.locations[node_index], assignment.Value(time_var)))

            if len(nodes) > 2: # 2 is from start to finish directly
                vehicles.append(Vehicle(nodes))

        return Solution(vehicles)
