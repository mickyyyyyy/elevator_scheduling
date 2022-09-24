## What we want working...
##
## - figure out adding and removing of pick up/ drop off
## - multiple threads (or timers) to show elevators working simultaneously
##   instead of in series.
## - make the list of floors for elevators into a heap (should be more
##   efficient).
## - show drop off and pick up on each elevator's floor map.
## - improve accuracy of determine_ticks
## - incorporate measurement of number of reactions ticks + look to improve
## - include elevator capacity, and could include further tracking of passengers
##   (meant to replicate knowledge from real life elevator systems, i.e. if an
##   elevator needs to pick up from a floor, we don't know how many passengers
##   are coming in, and vice versa for drop offs - could sense weight in the
##   elevator though and use this for capacity).
## - look into how real elevator systems work with a lot of falls

import math
import random
from time import *


# Constants

# Elevator
DEFAULT_SPEED = 1 # floors/tick
DEFAULT_TIME = 1 # seconds/tick
LAST_FLOOR = 0 # default starting floor

# Transportation system
ELEVATOR_NUMBER = 2 # the default number of elevators
DIRECTIONS = {'U', 'D'} # the default directions
LEVELS = {2 : '2',
          1 : '1',
          0 : 'G',
          -1 : 'B1',
          -2 : 'B2'} # the mapping from heights to floor numbers

# Keeps track of elevators if elevators are made externally to transport system
elevator_number = 0


class Passenger :
    """Passenger that uses the elevator."""

    def __init__(self, direction, startFloor) :
        """Creates a Passenger.

        Parameters:
            direction (char) -> the direction the Passenger wants to go in
                                (U for up and D for down).
            startFloor (int) -> the floor the passenger wants to move from.
        """
        self.direction = direction
        self.startFloor = startFloor

    def get_direction(self) :
        """Returns the direction the passenger desires to go in.
        """
        return self.direction

    def get_start_floor(self) :
        """Returns the floor the passenger desires to move from.
        """
        return self.startFloor

    def nominate_floor(self, elevator, floor) :
        """Allows the passenger to nominate which floor they would like to get
        off at.

        Parameters:
            elevator (Elevator) -> the elevator the passenger is on.
            floor (int) -> the floor number to get off at.
        """
        if floor not in elevator.get_floors() :
            elevator.add_floor(floor, 'D')


class Floor :
    """Represents a floor in the building."""

    def __init__(self, height, actions=None) :
        """Creates a floor representation.

        Parameters:
            height (int) -> the height the floor is at.
            actions (List<char>) -> all the actions required on the given floor.
        """
        self.height = height

        if not actions :
            self.actions = []
        else :
            self.actions = actions

    def get_height(self) :
        """Returns the height of the floor.
        """
        return self.height

    def add_action(self, action) :
        """Adds an action to be completed.

        Parameters:
            action (char) -> the action to add.
        """
        if action not in self.actions :
            self.actions.append(action)

    def remove_action(self, action) :
        """Removes an action which has been completed.

        Parameters:
            action (char) -> the action to remove.
        """ 
        if action in self.actions :
            self.actions.remove(action)

    def get_actions(self) :
        """Returns the actions required on that floor.
        """
        return self.actions

    def get_priority(self) :
        """Deprecated -> in use when trying to determine path based on
        prioritising drop offs over pick ups.

        Returns the priority of this floor, or None if we have no actions on
        this floor.
        """
        if 'D' in self.actions :
            return 0
        elif 'P' in self.actions :
            return 1
        else :
            return None

    def __hash__(self) :
        return self.get_height()

    def __eq__(self, other) :
        return self.get_height() == other.get_height()

    def __lt__(self, other) :
        return self.get_height() < other.get_height()

    def __gt__(self, other) :
        return self.get_height() > other.get_height()

    def __sub__(self, other):
        return self.get_height() - other.get_height()


class Elevator :
    """Elevator which moves passengers."""

    def __init__(self, floorDetails, lastFloor, name=None, floorPlan=None, speed=None,
                 openingTime=None, direction=None, state=None,
                 floorActions=None, operational=True, opened=False) :
        """Creates an elevator.
        (need to add dict mapping floor numbers to list of chars associated with the
        actions this elevator is completing at each floor).

        Parameters:
            floorDetails (Dict<int:Floor>) -> A map between elevations and floors.
            lastFloor (int) -> the last floor the elevator handshaked.
            name (str) -> the name of the elevator (for printing).
            floorPlan (Dict<int:str>) -> the names for each elevation the elevator
                                         can reach.
            speed (int) -> the speed of the elevator (floors/second).
            openingTime (int) -> the time the elevator will be open for.
            direction (char) -> the direction the elevator is going in
                                U -> up
                                D -> down
                                None -> stationary
            state (str) -> Represents the state of the elevator.
                           "Picking up", "Dropping off", "Both" or None (not used).
                           Could have "Moving up to pick up passenger from level 2"
                           or something more descriptive?
            floorActions (List<Floor>) -> the floor details if we have an action to
                                          complete.
            operational (Bool) -> True if the elevator is operational, False
                                  otherwise (not in use).
            opened (Bool) -> True if the elevators doors are open, False otherwise
        """
        
        # Keep track of specific properties of the last floor this elevator
        # travelled to.
        self.floorDetails = floorDetails
        self.lastFloor = self.floorDetails[lastFloor]

        # Designate a name for the elevator if not given
        if name is None :
            global elevator_number
            self.name = "E{}".format(elevator_number)
            elevator_number += 1
        else :
            self.name = name

        # Nominate a floor plan the elevator can use
        if floorPlan is None :
            self.floorPlan = LEVELS
        else :
            self.floorPlan = floorPlan

        # Determine the speed of the elevator
        if speed is None :
            self.speed = DEFAULT_SPEED
        else :
            self.speed = speed

        # Determine the time the elevator takes to open and shut
        if openingTime is None :
            self.openingTime = DEFAULT_TIME
        else :
            self.openingTime = openingTime

        self.direction = direction
        self.state = state

        # Alternative data structure for elevator path
        #if floors is None :
            # Use a list, heap or tree?
            # Start with a list ->
            #     insert : O(n)
            #     read : O(1)
            #     remove : O(n) -> heap is better
        #    self.floors = {}
        #else :
        #    self.floors = floors

        # Used a list implementation - actions at each floor
        if floorActions is None :
            self.floorActions = []
        else :
            self.floorActions = floorActions

        # States for elevator
        self.operational = operational
        self.opened = opened
        
    def get_last_floor(self) :
        """Returns the last floor the elevator handshaked."""
        return self.lastFloor

    def set_last_floor(self, lastFloor) :
        """Sets the last floor the elevator handshaked.

        Parameters:
            lastFloor (int) -> the last floor the elevator handshaked.
        """
        self.lastFloor = self.floorDetails[lastFloor]

    def get_next_floor(self) :
        """Reads the next floor the elevator will travel to."""
        if self.get_floors() :
            floor = self.get_floors()[0]
        else :
            floor = None

        return floor
    
    def get_name(self) :
        """Returns the name of the elevator."""
        return self.name

    def get_speed(self) :
        """Returns the speed of the elevator."""
        return self.speed

    def set_speed(self, speed) :
        """Sets the speed of the elevator (shouldn't use this).

        Parameters:
            speed (int) -> the new speed of the elevator.
        """
        self.speed = speed

    def get_opening_time(self) :
        """Returns the opening time of the elevator doors.
        """
        return self.openingTime

    def set_direction(self, direction) :
        """Sets the direction of the elevator.

        Parameters:
            direction (char) -> the desired direction for the elevator. 
        """
        self.direction = direction

    def get_direction(self) :
        """Returns the direction the elevator is going in."""
        return self.direction

    def set_opened(self, opened) :
        """Sets the elevator to the desired opened state.

        Parameters:
            opened (Bool) -> True if the elevator doors are open, False
                             otherwise.
        """
        self.opened = opened

    def get_opened(self) :
        """Returns the opened state of the elevator.
        """
        return self.opened

    def get_floors(self) :
        """Returns the floors the elevator needs to travel to (in order).
        """
        return self.floorActions

    def move(self) :
        """Moves the elevator in the current direction.
        """
        if self.get_direction() == 'U' :
            # Caps upper limit of elevator
            self.set_last_floor(min(self.get_last_floor().get_height() + 1,
                                max(self.floorPlan.keys())))
            
        elif self.get_direction() == 'D' :
            # Caps lower limit of elevator
            self.set_last_floor(max(self.get_last_floor().get_height() - 1,
                                min(self.floorPlan.keys())))

    def add_floor(self, floor, states) :
        """Adds the floor details for which the elevator needs to visit.

        Parameters:
            floor (Floor) -> the floor we are adding.
            states (List<char>) -> the reason why we are going to this floor.
                           'D' for dropping off, 'P' for picking up.
        """
        
        # Only insert into list if we aren't already going to this floor
        if floor not in self.floorActions :

            index = 0
            while index < len(self.floorActions) :

                # Find the spot in the path when this floor will be visited
                if (self.direction == 'U' and
                    floor > self.lastFloor and
                    floor < self.floorActions[index]) \
                   or (self.direction == 'D' and
                    floor < self.lastFloor and
                    floor > self.floorActions[index]) :
                    break

                index += 1

            # Insert
            self.floorActions.insert(index, floor)

        # Add what we are doing at this floor
        else :
            for state in states :
                if state not in floor.get_actions() :
                    floor.add_action(state)

    def remove_floor(self, floor, states) :
        """Removes the floor number as a floor the elevator has already visited.

        Parameters:
            floor (Floor) -> the floor to remove.
            states (List<char>) -> the reason(s) why we are travelling to this floor.
        """
        if floor in self.floorActions :

            # Remove each state
            for state in states :
                floor.remove_action(state)

            # Remove the floor if there are no actions for it anymore
            if not floor.get_actions() :
                self.floorActions.remove(floor)

    def floor_str(self, floor) :
        """Returns the string representation at a given floor.

        Parameters:
            floor (Floor) -> the floor we want a representation for.
        """

        # Shows where the elevator is
        if floor == self.get_last_floor() :
            if self.get_opened() :
                return "[  ]"
            else :
                return " [] "
                
        else :
            return "    "

        # Prints the actions required for each floor
        if floor in self.floorActions :
            floorRepr = " "

            # Adds each action to the representation
            for action in floor.get_actions() :
                floorRepr += action

            # Aligns starting string representations on each floor
            for _ in range(2 - len(floor.get_actions())) :
                floorRepr += " "

            return floorRepr

    def get_picking_up(self) :
        """Returns the floors where we are picking up passengers.
        """
        floors = []
        for floor in self.get_floors() :

            # Adds floors with a pick up priority
            if floor.get_priority() == 1 :
                floors.append(floor)

        return floors

    def get_dropping_off(self) :
        """Returns the floors where we are dropping off passengers.
        """
        floors = []
        for floor in self.get_floors() :
            
            # Adds floors with a drop off priority
            if floor.get_priority() == 0 :
                floors.append(floor)

        return floors

    def tick(self) :
        """Allows the elevator to act for one tick."""

        # Check which direction we need to move in
        if self.get_floors() :

            # Shortcuts
            lastFloor = self.get_last_floor()
            elevation = self.get_next_floor().get_height() -\
                        lastFloor.get_height()

            # Set the direction based on the next floor we need to travel to
            if elevation < 0 :
                self.set_direction('D')
            elif elevation > 0 :
                self.set_direction('U')
            else :
                self.set_direction(None)

        # Determine the next action we need to take
        if not self.get_last_floor() in self.get_floors() :
            if self.get_opened() :
                self.set_opened(False)
            else :
                self.move()
        else :
            self.set_opened(True)
            # Only want to remove the actions we actually completed -> will need to be changed
            self.remove_floor(lastFloor, lastFloor.get_actions())           
            
    def determine_ticks(self, request) :
        """Heuristic -> determine the number of ticks we estimate it to take to
        complete the given request.

        Parameters:
            request (Request) -> the request we want to test.
        """
        
        # Set the tick counter to zero and create some shortcuts
        ticks = 0
        floor = request.get_floor()
        lastFloor = self.get_last_floor()
        nextFloor = self.get_next_floor()
        elevation = self.get_last_floor() - floor

        # Get the direction we are going in as a unit vector
        if elevation :
            direction = elevation // abs(elevation)

        # Going straight there without stops
        if not self.get_floors() or \
           (request.direction == self.direction and
           ((elevation > 0 and request.direction == 'U' and
           floor < nextFloor) or (elevation < 0 and
           request.direction == 'D' and floor > nextFloor) or
            elevation == 0)) :
            
            ticks = elevation // self.get_speed() + \
                    self.get_opening_time()
        
        # Otherwise, determine if the requestor's direction is the same as the
        # current direction of the elevator.
        elif request.direction == self.direction and \
             ((elevation > 0 and request.direction == 'U') or
              (elevation < 0 and request.direction == 'D') or
              elevation == 0) :

            # Tracks the floors we have visited in this path
            floorInd = 0
            
            for height in range(0, elevation, direction) :

                # Keeps track of the time it takes to move one floor
                ticks += 1 / self.get_speed()

                if floorInd < len(self.get_floors()) and \
                   self.get_floors()[floorInd].get_height() == height :

                    # Flooring tick once we open the doors and shut them
                    ticks = ticks // 1 + 2 * self.get_opening_time()
                    floorInd += 1

        # More than one turn around to pick up (could be implemented for a
        # better heuristic).
        else :
            ticks = None

        return ticks

    def __str__(self) :
        # Title line for elevator name
        start = "Elevator:   "
        output = start + str(self.get_name()) + "\n"

        for floor in self.floorPlan :
            
            # Formatting
            for _ in range(len(start) - 4 - len(self.floorPlan[floor])) :
                output += " "

            # Start the floor representation
            output += "{}: |{}|\n".format(self.floorPlan[floor], self.floor_str(floor))

        return output


class Request :
    """Request for a passenger to use the elevator."""

    def __init__(self, floor, direction, passenger, assigned=None, elevator=None,
                 completed=None) :
        """Creates a request.

        Parameters:
            floor (Floor) -> the floor the request was made on.
            direction (char) -> the direction the passenger wants to go in
            passenger (Passenger) -> the passenger making the request.
            assigned (Bool) -> True if an elevator has been assigned this request,
                               False otherwise.
                               If not given, assigned is False.
            elevator (Elevator) -> the elevator which has been assigned to complete
                                   this request.
            completed (Bool) -> whether this request has been completed or not.
        """
        
        # Initiate important characteristics of request
        self.floor = floor
        self.direction = direction
        self.passengers = [passenger]
        
        # Assuming a request starts as unassigned (unless otherwise given)
        if assigned is None or not assigned :
            self.assigned = False
            self.elevator = None
            self.completed = False
        else :
            self.assigned = assigned
            self.elevator = elevator
            self.completed = completed

    def assign(self, elevator) :
        """Assign this request to a given elevator.

        Parameters:
            elevator (Elevator) -> the elevator which is being assigned the request.
        """
        self.elevator = elevator
        self.assigned = True

    def complete(self) :
        """The designated elevator has completed the request.
        """
        self.completed = True

    def get_floor(self) :
        """Returns the floor number the requestor is on.
        """
        return self.floor

    def add_passengers(self, passengers) :
        """Adds a group of passengers to the request.

        Parameters:
            passengers (List<Passenger>) -> the passengers to add.
        """
        self.passengers.extend(passengers)

    def get_passengers(self) :
        """Returns the passenger that requested.
        """
        return self.passengers

    def get_direction(self) :
        """Returns the direction the requestor desires to travel.
        """
        return self.direction

    def is_assigned(self) :
        """Returns the state of assignment for the request.
        """
        return self.assigned

    def get_elevator(self) :
        """Returns the elevator (if any) which has been assigned to this request.
        """
        return self.elevator

    def is_complete(self) :
        """Returns the state of completion for the request.
        """
        return self.completed

    def __eq__(self, other) :
        # Check to see if the request starts at the same floor, has the same
        # direction AND that they both have the same completion status.
        #
        # (we don't care about the assigned status or the passenger, because
        # this will usually mean we assign the one that isn't assigned)
        
        if self.get_floor() == other.get_floor() and \
           self.get_direction() == other.get_direction() and \
           self.is_complete() == other.is_complete() :
            return True
        else :
            return False

    def __hash__(self) :
        num = 0

        # Making each digit unique based on completion status, direction and
        # height
        if self.is_complete() :
            num += 1
        if self.get_direction() == 'U' :
            num += 10

        num += self.get_floor().get_height() * 100

        return num


class TransportSystem :
    """Transport system to encapsulate elevators and passengers."""

    def __init__(self, elevators=None, levels=None, requests=None) :
        """Creates a transportation system.

        Parameters:
            elevators (List<Elevator>) -> the elevators which will be used to
                                          transport passsengers.
            levels (Dict<int:str>) -> relates floor names to elevations.
            requests (List<Request>) -> queue to allow passengers at each floor
                                        to request to use the elevator.
        """

        # Deal with floor plan (levels)
        if levels is None :
            self.levels = LEVELS
        else :
            self.levels = levels

        # Construct a dictionary which relates floor elevation with other floor
        # details
        self.floorDetails = {}
        for elevation in self.levels :
            self.floorDetails[elevation] = Floor(elevation)

        # Deal with elevators
        if elevators is None :
            self.elevators = self.make_default_elevators()
        else :
            self.elevators = elevators

        # Deal with requests
        if requests is None :
            self.requests = []
        else :
            self.requests = requests

    def make_default_elevators(self) :
        """Creates a number of elevators.
        """
        elevators = []
        for elevator in range(ELEVATOR_NUMBER) :
            elevators.append(Elevator(self.floorDetails, LAST_FLOOR))

        return elevators

    def get_elevators(self) :
        """Returns the elevators which are in the system.
        """
        return self.elevators
    
    def request(self, request) :
        """Passenger requesting to move from the given floor in the given
        direction.

        Parameters:
            request (Request) -> the request to add to our requests.
        """
        if request not in self.requests :
            self.requests.append(request)

    def get_requests(self) :
        """Returns the requests which have not been completed.
        """
        return self.requests

    def assign_request(self, request, elevator, state) :
        """Assigns a request to an elevator.

        Parameters:
            request (Request) -> the request being assigned.
            elevator (Elevator) -> the elevator being designated.
            state (char) -> the reason for designation
                            (should be changed to action which should be changed
                             to it's own class (probably can remove floor class?
                             -> picking up from level 2 etc.)
        """
        if not request.is_assigned() :
            elevator.add_floor(request.get_floor(), state)
            request.assign(elevator)

    def tick(self) :
        """Ticks the system.
        """

        print(self)

        # Making a shallow copy to iterate through incase a request was recently
        # completed
        requests = self.requests.copy()        
        reqsRemoved = 0
        
        # Check each request
        for rID, request in enumerate(requests) :
            floor = request.get_floor()

            # Try assign requests which have not been assigned yet
            if not request.is_assigned() :

                # Determine the optimal elevator to assign this request to
                optElevator = None
                minTicks = math.inf

                for elevator in self.get_elevators() :
                    elevatorTicks = elevator.determine_ticks(request)

                    # Found a new optimal elevator
                    if elevatorTicks and elevatorTicks < minTicks :
                        optElevator = elevator
                        minTicks = elevatorTicks

                # If we found an optimal elevator, then assign the request
                if optElevator :
                    self.assign_request(request, optElevator, 'P')

            # Check if we have completed assigned requests
            else :
                
                if request.get_elevator().get_last_floor() == \
                   floor :

                    # Change the request to completed
                    request.complete()
                    compRequest = self.requests.pop(rID - reqsRemoved)
                    reqsRemoved += 1
                    
                    # Determines which floors the passenger can nominate
                    possibleFloors = []
                    elevator = request.get_elevator()
                    for floor in list(self.levels.keys()) :
                        if (request.get_direction() == 'U' and \
                           floor > request.get_floor().get_height()) or \
                           (request.get_direction() == 'D' and \
                             floor < request.get_floor().get_height()) :
                            possibleFloors.append(floor)

                    # Choose a random floor for each passenger
                    for passenger in request.get_passengers() :
                        floor = self.floorDetails[random.choice(
                            possibleFloors)]
                        passenger.nominate_floor(elevator, floor)
        
        # Allow each elevator to operate on whatever actions it has to complete
        for elevator in self.get_elevators() :

            # Will make this multi-threaded to see each elevator tick at once
            for _ in range(elevator.get_speed()) :
                elevator.tick()

    def add_request(self, weights=None, direction=None) :
        """Adds a request on a floor given the probability at each height.

        Parameters:
            weights (Dict<int:int>)) -> weights associated with the probability of
                                        each floor being the requested floor.
                                        If not given, defaults to an equal
                                        probability for each floor.
            direction (char) -> the desired direction for the request.
        """

        # Limitation on which floors we want to spawn passengers
        if not weights :
            weights = {}
            for height in self.levels.keys() :
                
                # Equal chance of each floor
                weights[height] = 1/len(self.levels)

        # Choose floor
        floorNum = random.choices(list(weights.keys()), list(weights.values()))[0]

        # Remove the direction if it isn't valid for the level chosen
        directions = DIRECTIONS.copy()
        if floorNum == max(self.levels.keys()) :
            directions.remove('U')
        elif floorNum == min(self.levels.keys()) :
            directions.remove('D')

        # Choose a direction
        if not direction or direction not in directions :
            direction = random.choice(list(directions))

        # Make the request
        floor = self.floorDetails[floorNum]
        request = Request(floor, direction, Passenger(direction, floor))
        self.request(request)

    def simulation_step(self, requests) :
        """Acts as one step in the simulation process.

        Parameters:
            requests (int) -> the number of requests to add at each step.
        """
        
        # Add some random requests
        for _ in range(requests) :
            self.add_request()
            
        self.tick()

    def simulation(self, steps, requests) :
        """Simulates the system allocating elevators in order to move passengers.

        Parameters:
            steps (int) -> the number of ticks for which we want to be adding
                           requests for.
            requests (int) -> the number of requests to add at each tick.
        """
        # First part of the simulation -> a specific number of steps where
        # passengers request
        for _ in range(steps) :
            self.simulation_step(requests)
            sleep(1)

        # After all these requests come through, transport every passenger where
        # they want to go, and finish the simulation
        while not self.is_solved() :
            
            # Not requesting, just ticking...
            self.simulation_step(0)
            sleep(1)

    def is_solved(self) :
        """Tells us whether the elevator system has transported every passenger to
        their desired destination.
        """
        
        # All elevators need to be idle, closed, and not have any passengers
        # to pick up
        for elevator in self.elevators :
            if elevator.get_opened() or elevator.get_floors() :
                return False

        # Shows the solved state if the simulation has finished
        print(self)
        
        return True

    def __str__(self) :
        # Start of the title
        start = "Elevators -"
        output = start

        for elevator in self.elevators :
            # Put the names of each elevator as headings
            output += "  {}  ".format(elevator.get_name())

        # Title for passenger requests
        output += " P  \n"
        
        for floor in self.levels.keys() :
            floorDets = self.floorDetails[floor]
            
            # Format level names in line with elevator titles
            for _ in range(len(start) + - len(self.levels[floor]) - 2) :
                output += " "
                
            # Print each level's name
            output += "{}: ".format(self.levels[floor])
            
            for elevator in self.elevators :
                
                # Print each elevator's floor
                output += "|{}|".format(elevator.floor_str(floorDets))

                # Format floor values with elevator names
                for _ in range(len(elevator.get_name()) -
                               len(elevator.floor_str(floorDets)) - 1) :
                    output += " "

            # Print the requests from the passengers
            output += " "
            requestStr = ""
            for request in self.requests :
                if floorDets == request.floor and \
                   request.get_direction() not in requestStr:
                    requestStr += request.get_direction()

            output += requestStr + "\n"
            
        return output
